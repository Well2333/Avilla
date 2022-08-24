from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING

from avilla.core.cell.cells import Nick, Privilege, Summary
from avilla.core.message import Message
from avilla.core.skeleton.message import MessageTrait
from avilla.core.skeleton.privilege import Mute
from avilla.core.skeleton.scene import SceneTrait
from avilla.core.skeleton.summary import SummaryTrait
from avilla.core.traitof.context import prefix, raise_for_no_namespace, scope
from avilla.core.traitof.recorder import default_target, impl, pull, query
from avilla.core.utilles.selector import Selector

if TYPE_CHECKING:
    from graia.amnesia.message import MessageChain

    from avilla.core.relationship import Relationship


raise_for_no_namespace()

with scope("group"), prefix("group"):

    @default_target(MessageTrait.send)
    def send_group_message_default_target(rs: Relationship):
        return rs.mainline

    @impl(MessageTrait.send)
    async def send_group_message(
        rs: Relationship, target: Selector, message: MessageChain, *, reply: Selector | None = None
    ) -> Selector:
        serialized_msg = await rs.protocol.serialize_message(message)
        result = await rs.account.call(
            "sendGroupMessage",
            {
                "__method__": "post",
                "target": int(target.pattern["group"]),
                "messageChain": serialized_msg,
                **({"quote": reply.pattern["message"]} if reply is not None else {}),
            },
        )
        return Selector().land(rs.land).group(target.pattern["group"]).message(result["messageId"])

    @impl(MessageTrait.revoke)
    async def revoke_group_message(rs: Relationship, message: Selector):
        await rs.account.call(
            "recall",
            {
                "__method__": "post",
                "messageId": int(message.pattern["message"]),
                "target": int(message.pattern["group"]),
            },
        )

    @impl(Mute.mute)
    async def mute_member(rs: Relationship, target: Selector, duration: timedelta):
        privilege_info = await rs.pull(Privilege, target)
        if not privilege_info.effective:
            raise PermissionError()  # TODO: error message, including Summary info
        time = max(0, min(int(duration.total_seconds()), 2592000))  # Fix time parameter
        if not time:
            return
        await rs.account.call(
            "mute",
            {
                "__method__": "post",
                "target": int(target.pattern["group"]),
                "memberId": int(target.pattern["member"]),
                "time": time,
            },
        )

    @impl(Mute.unmute)
    async def unmute_member(rs: Relationship, target: Selector):
        privilege_info = await rs.pull(Privilege, target)
        if not privilege_info.effective:
            raise PermissionError()  # TODO: error message, including Summary info
        await rs.account.call(
            "unmute",
            {
                "__method__": "post",
                "target": int(target.pattern["group"]),
                "memberId": int(target.pattern["member"]),
            },
        )

    @impl(Mute.mute_all)
    async def group_mute_all(rs: Relationship, target: Selector):
        await rs.account.call(
            "muteAll",
            {
                "__method__": "post",
                "target": int(target.pattern["group"]),
            },
        )

    @impl(Mute.unmute_all)
    async def group_unmute_all(rs: Relationship, target: Selector):
        await rs.account.call(
            "unmuteAll",
            {
                "__method__": "post",
                "target": int(target.pattern["group"]),
            },
        )

    @impl(SceneTrait.leave).pin("group")
    async def leave(rs: Relationship, target: Selector):
        await rs.account.call("quit", {"__method__": "post", "target": int(target.pattern["group"])})

    @impl(SceneTrait.remove_member)
    async def remove_member(rs: Relationship, target: Selector, reason: str | None = None):
        privilege_info = await rs.pull(Privilege, target)
        if not privilege_info.effective:
            raise PermissionError()  # TODO: error message, including Summary info
        await rs.account.call(
            "kick",
            {"__method__": "post", "target": int(target.pattern["group"]), "memberId": int(target.pattern["member"])},
        )

    @pull(Summary).of("group")
    async def get_summary(rs: Relationship, target: Selector | None) -> Summary:
        assert target is not None
        result = await rs.account.call(
            "groupConfig",
            {"__method__": "get", "target": int(target.pattern["group"])},
        )
        return Summary(describe=Summary, name=result["name"], description=None)

    @impl(SummaryTrait.set_name).pin("group")
    async def group_set_name(rs: Relationship, target: Selector, name: str):
        await rs.account.call(
            "groupConfig",
            {"__method__": "post", "target": int(target.pattern["group"]), "config": {"name": name}},
        )

    @pull(Nick).of("group.member")
    async def get_member_nick(rs: Relationship, target: Selector | None) -> Nick:
        assert target is not None
        result = await rs.account.call(
            "memberInfo",
            {"__method__": "get", "target": int(target.pattern["group"]), "memberId": int(target.pattern["member"])},
        )
        return Nick(Nick, result["memberName"], result["memberName"], result["specialTitle"])

    @query(None, "group")
    async def get_groups(rs: Relationship, upper: None, predicate: Selector):
        result: list[dict] = await rs.account.call("groupList", {"__method__": "get"})
        for i in result:
            group = Selector().group(str(i["id"]))
            if predicate.match(group):
                yield group

    @query("group", "member")
    async def get_group_members(rs: Relationship, upper: Selector, predicate: Selector):
        result: list[dict] = await rs.account.call(
            "memberList", {"__method__": "get", "target": int(upper.pattern["group"])}
        )
        for i in result:
            member = Selector().group(str(i["group"]["id"])).member(str(i["id"]))
            if predicate.match(member):
                yield member
