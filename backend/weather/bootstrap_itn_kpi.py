from __future__ import annotations

from collections.abc import Callable

from django.conf import settings

from weather.services.national_indicator.protocols import (
    NationalIndicatorKpiDataSource,
)


def _default_builder() -> NationalIndicatorKpiDataSource:
    from weather.data_sources.national_indicator_fake import (
        FakeNationalIndicatorDataSource,
        FakeNationalIndicatorKpiDataSource,
    )
    from weather.data_sources.timescale import (
        TimescaleNationalIndicatorKpiDataSource,
    )

    if settings.MOCKED_DATA:
        return FakeNationalIndicatorKpiDataSource(
            fake=FakeNationalIndicatorDataSource()
        )
    return TimescaleNationalIndicatorKpiDataSource()


class ITNKpiDependencyProvider:
    _builder: Callable[[], NationalIndicatorKpiDataSource] = _default_builder

    @classmethod
    def set_builder(cls, builder: Callable[[], NationalIndicatorKpiDataSource]) -> None:
        cls._builder = builder

    @classmethod
    def get_dep(cls) -> NationalIndicatorKpiDataSource:
        return cls._builder()

    @classmethod
    def reset(cls) -> None:
        cls._builder = _default_builder
