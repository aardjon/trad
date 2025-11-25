"""
Implementation of the FilterFactory component.
"""

from typing import TYPE_CHECKING, Final, override

from trad.application.boundaries.database import RelationalDatabaseBoundary
from trad.application.boundaries.grade_parser import GradeParser
from trad.application.boundaries.http import HttpNetworkingBoundary
from trad.application.filters.regular.merge import MergeFilter
from trad.application.filters.regular.validation import DataValidationFilter
from trad.application.filters.sink.db_v1 import DbSchemaV1Filter
from trad.application.filters.source.osm import OsmSummitDataFilter
from trad.application.filters.source.teufelsturm import TeufelsturmDataFilter
from trad.kernel.boundaries.filters import Filter, FilterFactory, FilterStage
from trad.kernel.boundaries.settings import SettingsBoundary
from trad.kernel.di import DependencyProvider

if TYPE_CHECKING:
    from collections.abc import Callable


class AllFiltersFactory(FilterFactory):
    """
    The factory for creating all filters that should be executed.

    Filters are only instantiated when they are used.
    """

    def __init__(self, dependency_provider: DependencyProvider) -> None:
        """
        Create a new FilterFactory with the given [dependency_provider].
        """
        self.__dependency_provider = dependency_provider

    @override
    def create_filters(self, stage: FilterStage) -> list[Filter]:
        filter_classes: Final[dict[type[Filter], Callable[[], Filter]]] = {
            OsmSummitDataFilter: lambda: OsmSummitDataFilter(
                self.__dependency_provider.provide(HttpNetworkingBoundary)
            ),
            TeufelsturmDataFilter: lambda: TeufelsturmDataFilter(
                self.__dependency_provider.provide(HttpNetworkingBoundary),
                self.__dependency_provider.provide(GradeParser),
            ),
            MergeFilter: MergeFilter,
            DataValidationFilter: DataValidationFilter,
            DbSchemaV1Filter: lambda: DbSchemaV1Filter(
                self.__dependency_provider.provide(SettingsBoundary).get_output_dir(),
                self.__dependency_provider.provide(RelationalDatabaseBoundary),
            ),
        }
        return [
            filter_creator()
            for filter_class, filter_creator in filter_classes.items()
            if filter_class.get_stage() == stage
        ]
