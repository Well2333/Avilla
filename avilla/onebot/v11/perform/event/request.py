from __future__ import annotations

from datetime import datetime, timedelta
from typing import cast

from loguru import logger

from avilla.core.context import Context
from avilla.core.event import MetadataModified, ModifyDetail, RelationshipCreated, RelationshipDestroyed
from avilla.core.ryanvk.descriptor.event import EventParse
from avilla.core.selector import Selector
from avilla.onebot.v11.collector.connection import ConnectionCollector
from avilla.standard.core.activity import ActivityTrigged
from avilla.standard.core.privilege import MuteInfo, Privilege
from avilla.standard.qq.event import PocketLuckyKingNoticed
from avilla.standard.qq.honor import Honor
from avilla.standard.core.request import RequestEvent
from avilla.core.request import Request


class OneBot11EventRequestPerform((m := ConnectionCollector())._):
    m.post_applying = True

    @EventParse.collect(m, "request.friend")
    async def friend(self, raw: dict):
        self_id = raw["self_id"]
        account = self.connection.accounts.get(self_id)
        if account is None:
            logger.warning(f"Unknown account {self_id} received message {raw}")
            return
        request = Request(
            raw["flag"],
            account.info.platform.land,
            Selector().land("qq").user(str(raw["user_id"])),
            Selector().land("qq").user(str(raw["user_id"])),
            account,
            datetime.fromtimestamp(raw["time"]),
        )
        return RequestEvent(
            Context(
                account,
                request.sender,
                request.sender,
                request.scene,
                account.route,
            ),
            request,
        )

    @EventParse.collect(m, "request.group.add")
    @EventParse.collect(m, "request.group.invite")
    async def group(self, raw: dict):
        self_id = raw["self_id"]
        account = self.connection.accounts.get(self_id)
        if account is None:
            logger.warning(f"Unknown account {self_id} received message {raw}")
            return
        request = Request(
            raw["flag"],
            account.info.platform.land,
            Selector().land("qq").group(str(raw["group_id"])),
            Selector().land("qq").user(str(raw["user_id"])),
            account,
            datetime.fromtimestamp(raw["time"]),
        )
        return RequestEvent(
            Context(
                account,
                request.sender,
                request.sender,
                request.scene,
                account.route,
            ),
            request,
        )
