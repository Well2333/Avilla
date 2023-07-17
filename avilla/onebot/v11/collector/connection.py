from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, TypeVar

from avilla.core.ryanvk._runtime import processing_protocol
from avilla.core.ryanvk.collector.base import (
    Access,
    BaseCollector,
    PerformTemplate,
)

if TYPE_CHECKING:
    from avilla.onebot.v11.net.ws_client import OneBot11WsClientNetworking
    from avilla.onebot.v11.protocol import OneBot11Protocol


T = TypeVar("T")
T1 = TypeVar("T1")


class ConnectionBasedPerformTemplate(PerformTemplate):
    __collector__: ClassVar[ConnectionCollector]

    protocol: Access[OneBot11Protocol] = Access()
    connection: Access[OneBot11WsClientNetworking] = Access()


class ConnectionCollector(BaseCollector):
    post_applying: bool = False

    @property
    def _(self):
        upper = super().get_collect_template()

        class PerformTemplate(
            ConnectionBasedPerformTemplate,
            upper,
        ):
            __native__ = True

        return PerformTemplate

    def __post_collect__(self, cls: type[ConnectionBasedPerformTemplate]):
        super().__post_collect__(cls)
        if self.post_applying:
            if (protocol := processing_protocol.get(None)) is None:
                raise RuntimeError("expected processing protocol")
            protocol.isolate.apply(cls)
