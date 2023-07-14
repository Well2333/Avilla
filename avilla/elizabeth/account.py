from __future__ import annotations

from typing import TYPE_CHECKING, Any

from avilla.core.account import BaseAccount
from avilla.core.context import Context
from avilla.core.selector import Selector
from avilla.elizabeth.connection.util import CallMethod
from avilla.elizabeth.connection.base import ElizabethNetworking

if TYPE_CHECKING:
    from ..elizabeth.protocol import ElizabethProtocol


class ElizabethAccount(BaseAccount):
    protocol: ElizabethProtocol

    async def get_context(self, target: Selector, *, via: Selector | None = None) -> Context:
        ...

    @property
    def connection(self) -> ElizabethNetworking:
        return self.protocol.service.get_connection(self.route['account'])

    @property
    def available(self) -> bool:
        return self.connection.alive

    async def call(self, endpoint: str, params: dict[str, Any] | None = None) -> Any:
        params = params or {}
        method: CallMethod = params.pop("__method__")
        if params.pop("__use_session__", True):
            await self.connection.wait_for_available()  # wait until session_key is present
            session_key = self.connection.session_key
            params["sessionKey"] = session_key
        return await self.connection.call(method, endpoint, params)
