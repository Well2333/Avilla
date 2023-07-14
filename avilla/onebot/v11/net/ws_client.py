from __future__ import annotations

import asyncio
import json
from collections import ChainMap
from typing import TYPE_CHECKING, cast

import aiohttp
from loguru import logger
from yarl import URL

from avilla.core._vendor.dataclasses import dataclass
from avilla.onebot.v11.net.base import OneBot11Networking
from avilla.standard.core.account import AccountUnregistered
from launart import Launchable
from launart.manager import Launart
from launart.utilles import any_completed

from ..account import OneBot11Account

if TYPE_CHECKING:
    from ..protocol import OneBot11Protocol


@dataclass
class OneBot11WsClientConfig:
    endpoint: URL
    access_token: str | None = None


class OneBot11WsClientNetworking(OneBot11Networking["OneBot11WsClientNetworking"], Launchable):
    id = "onebot/v11/connection/websocket/client"

    required: set[str] = set()
    stages: set[str] = {"preparing", "blocking", "cleanup"}

    config: OneBot11WsClientConfig
    connection: aiohttp.ClientWebSocketResponse | None = None

    def __init__(self, protocol: OneBot11Protocol, config: OneBot11WsClientConfig) -> None:
        super().__init__(protocol)
        self.config = config

    async def message_receive(self):
        if self.connection is None:
            raise RuntimeError("connection is not established")

        async for msg in self.connection:
            logger.debug(f"{msg=}")

            if msg.type in {aiohttp.WSMsgType.CLOSE, aiohttp.WSMsgType.ERROR, aiohttp.WSMsgType.CLOSED}:
                self.close_signal.set()
                break
            elif msg.type == aiohttp.WSMsgType.TEXT:
                data: dict = json.loads(cast(str, msg.data))
                yield self, data
        else:
            await self.connection_closed()

    async def send(self, payload: dict):
        if self.connection is None:
            raise RuntimeError("connection is not established")

        await self.connection.send_json(payload)

    async def wait_for_available(self):
        await self.status.wait_for_available()

    def get_staff_components(self):
        return {"connection": self, "protocol": self.protocol, "avilla": self.protocol.avilla}

    def get_staff_artifacts(self):
        return ChainMap(self.protocol.isolate.artifacts, self.protocol.avilla.isolate.artifacts)

    @property
    def alive(self):
        return self.connection is not None and not self.connection.closed

    async def connection_daemon(self, manager: Launart, session: aiohttp.ClientSession):
        avilla = self.protocol.avilla
        while not manager.status.exiting:
            async with session.ws_connect(
                self.config.endpoint,
                headers={"Authorization": f"Bearer {access_token}"}
                if (access_token := self.config.access_token) is not None
                else None,
            ) as self.connection:
                logger.info(f"{self} Websocket client connected")
                self.close_signal.clear()
                close_task = asyncio.create_task(self.close_signal.wait())
                receiver_task = asyncio.create_task(self.message_handle())
                sigexit_task = asyncio.create_task(manager.status.wait_for_sigexit())

                done, pending = await any_completed(
                    sigexit_task,
                    close_task,
                    receiver_task,
                )
                if sigexit_task in done:
                    logger.info(f"{self} Websocket client exiting...")
                    await self.connection.close()
                    self.close_signal.set()
                    self.connection = None
                    for v in list(avilla.accounts.values()):
                        if v.protocol is self.protocol:
                            _account = int(v.route["account"])
                            if _account in self.accounts:
                                del self.accounts[_account]
                    return
                if close_task in done:
                    receiver_task.cancel()
                    logger.warning(f"{self} Connection closed by server, will reconnect in 5 seconds...")
                    accounts = {str(i) for i in self.accounts.keys()}
                    # TODO: unregister all accounts, or cause inconsistency
                    for n in list(avilla.accounts.keys()):
                        logger.debug(f"Unregistering onebot(v11) account {n}...")
                        account = cast("OneBot11Account", avilla.accounts[n].account)
                        account.status.enabled = False
                        await avilla.broadcast.postEvent(AccountUnregistered(avilla, avilla.accounts[n].account))
                        if n.follows("land(qq).account") and n["account"] in accounts:
                            del avilla.accounts[n]
                    self.accounts.clear()
                    await asyncio.sleep(5)
                    logger.info(f"{self} Reconnecting...")
                    continue

    async def launch(self, manager: Launart):
        async with self.stage("preparing"):
            session = aiohttp.ClientSession()

        async with self.stage("blocking"):
            await self.connection_daemon(manager, session)

        async with self.stage("cleanup"):
            await session.close()
            self.connection = None
