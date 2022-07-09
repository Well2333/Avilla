from __future__ import annotations

import inspect
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Callable, ClassVar, Coroutine, Generic, Iterable, TypeVar
from avilla.core.account import AccountSelector
from avilla.core.event import AvillaEvent

from graia.amnesia.message.element import Element
from graia.broadcast.utilles import run_always_await
from typing_extensions import Self

from loguru import logger

if TYPE_CHECKING:
    from avilla.core.protocol import BaseProtocol

def event(event_type: str):
    def wrapper(func):
        func.__event_parser__ = event_type
        return func
    return wrapper


_P = TypeVar("_P", bound="BaseProtocol")

class AbstractEventParser(ABC, Generic[_P]):
    event_parser: dict[str, Callable[[Self, _P, AccountSelector, dict], Element | Coroutine[None, None, Element]]] = {}

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()
        cls.event_parser = {}
        for mro in reversed(inspect.getmro(cls)):
            if issubclass(mro, AbstractEventParser):
                cls.event_parser.update(mro.event_parser)
        members = inspect.getmembers(cls)
        for _, value in members:
            if callable(value) and getattr(value, "__event_parser__", False):
                cls.event_parser[value.__event_parser__] = value

    @abstractmethod
    def get_event_type(self, raw: dict) -> str:
        ...

    async def parse_event(self, protocol: _P, account: AccountSelector, raw: dict, *, error: bool = False) -> AvillaEvent:
        element_type = self.get_event_type(raw)
        deserializer = self.event_parser.get(element_type)
        if deserializer is None:
            if error:
                raise NotImplementedError(f"Event type {element_type} is not supported.")
            logger.warning(f"Event type {element_type} is not supported by {self.__class__.__name__}", raw)
        return await run_always_await(deserializer, self, protocol, account, raw)  # type: ignore
