from __future__ import annotations

from avilla.core.ryanvk import Capability, Fn, TargetOverload
from avilla.core.selector import Selector
from graia.amnesia.message import MessageChain

# MessageFetch => rs.pull(Message, target=...)


class MessageSend(Capability):
    @Fn.with_overload({TargetOverload(): ["target"]})
    async def send(self, target: Selector, message: MessageChain, *, reply: Selector | None = None) -> Selector:
        ...


class MessageRevoke(Capability):
    @Fn.with_overload({TargetOverload(): ["target"]})
    async def revoke(self, target: Selector) -> None:
        ...


class MessageEdit(Capability):
    @Fn.with_overload({TargetOverload(): ["target"]})
    async def edit(self, target: Selector, content: MessageChain) -> None:
        ...
