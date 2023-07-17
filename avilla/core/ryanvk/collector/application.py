from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, TypeVar

from avilla.core.ryanvk._runtime import processing_application, processing_isolate
from avilla.core.ryanvk.collector.base import Access, BaseCollector, PerformTemplate

if TYPE_CHECKING:
    from avilla.core.application import Avilla


T = TypeVar("T")
T1 = TypeVar("T1")


class ApplicationBasedPerformTemplate(PerformTemplate):
    __collector__: ClassVar[ApplicationCollector]
    avilla: Access[Avilla] = Access()


class ApplicationCollector(BaseCollector):
    post_applying: bool = False

    def __init__(self):
        super().__init__()

    @property
    def _(self):
        upper = super().get_collect_template()

        class LocalPerformTemplate(
            ApplicationBasedPerformTemplate,
            upper,
        ):
            __native__ = True

        return LocalPerformTemplate

    def __post_collected__(self, cls: type[ApplicationBasedPerformTemplate]):
        super().__post_collected__(cls)
        if self.post_applying:
            if (application := processing_application.get(None)) is None:
                if (isolate := processing_isolate.get(None)) is not None:
                    isolate.apply(cls)
                return

            application.isolate.apply(cls)
