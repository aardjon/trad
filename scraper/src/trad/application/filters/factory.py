"""
Implementation of the FilterFactory component.
"""

from collections.abc import Callable, Iterator
from typing import Final, override

from trad.application.boundaries.database import RelationalDatabaseBoundary
from trad.application.boundaries.grade_parser import GradeParser
from trad.application.boundaries.http import HttpNetworkingBoundary
from trad.application.filters.regular.merge import MergeFilter
from trad.application.filters.regular.validation import DataValidationFilter
from trad.application.filters.sink.db_v1 import DbSchemaV1Filter
from trad.application.filters.source.osm import OsmSummitDataFilter
from trad.application.filters.source.teufelsturm import TeufelsturmDataFilter
from trad.kernel.boundaries.filters import Filter, FilterFactory
from trad.kernel.boundaries.settings import SettingsBoundary
from trad.kernel.di import DependencyProvider


class AllFiltersFactory(FilterFactory):
    """
    The factory for creating all filters that should be executed.

    Filters are only instantiated when they are used.
    """

    def __init__(self, dependency_provider: DependencyProvider) -> None:
        """
        Create a new FilterFactory with the given [dependency_provider].
        """
        self._filter_classes: Final[dict[type[Filter], Callable[[], Filter]]] = {
            OsmSummitDataFilter: lambda: OsmSummitDataFilter(
                dependency_provider.provide(HttpNetworkingBoundary)
            ),
            TeufelsturmDataFilter: lambda: TeufelsturmDataFilter(
                dependency_provider.provide(HttpNetworkingBoundary),
                dependency_provider.provide(GradeParser),
            ),
            MergeFilter: MergeFilter,
            DataValidationFilter: DataValidationFilter,
            DbSchemaV1Filter: lambda: DbSchemaV1Filter(
                dependency_provider.provide(SettingsBoundary).get_output_dir(),
                dependency_provider.provide(RelationalDatabaseBoundary),
            ),
        }
        """ Mapping of all concrete Filter classes and their creation function. """

        self._stages: Final[list[list[type[Filter]]]] = [
            [OsmSummitDataFilter, TeufelsturmDataFilter],
            [MergeFilter],
            [DataValidationFilter],
            [DbSchemaV1Filter],
        ]
        """
        List of all stages and all concrete Filters that must be run in each of them.

        The stages are meant to be executed in that order (starting with the first Filter list).
        """

    @override
    def get_stage_count(self) -> int:
        return len(self._stages)

    @override
    def iter_filter_stages(self) -> Iterator[list[Filter]]:
        for stage_filters in self._stages:
            yield [self._filter_classes[filter_class]() for filter_class in stage_filters]
