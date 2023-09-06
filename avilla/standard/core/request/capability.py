from __future__ import annotations

from avilla.core.ryanvk import Capability, Fn, TargetOverload
from avilla.core.selector import Selector


class RequestCapability(Capability):
    @Fn.with_overload({TargetOverload(): ["target"]})
    async def accept(self, target: Selector):
        ...

    @Fn.with_overload({TargetOverload(): ["target"]})
    async def reject(self, target: Selector, reason: str | None = None, forever: bool = False):
        ...

    @Fn.with_overload({TargetOverload(): ["target"]})
    async def cancel(self, target: Selector):
        ...

    @Fn.with_overload({TargetOverload(): ["target"]})
    async def ignore(self, target: Selector):
        ...
