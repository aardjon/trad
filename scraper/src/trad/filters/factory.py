"""
Implementation of the FilterFactory component.
"""

from typing import Final, override

from trad.core.boundaries.filters import Filter, FilterFactory, FilterStage
from trad.crosscuttings.di import DependencyProvider
from trad.filters.initialization import PipeInitializingFilter
from trad.filters.optimization import PipeOptimizingFilter
from trad.filters.osm import OsmSummitDataFilter
from trad.filters.teufelsturm import TeufelsturmDataFilter


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
        filter_classes: Final = [
            PipeInitializingFilter,
            OsmSummitDataFilter,
            TeufelsturmDataFilter,
            PipeOptimizingFilter,
        ]
        return [
            # Ignoring the MyPy warning "Cannot instantiate abstract class" here because it is a
            # known False Positive which will hopefully go away in some future version.
            # See also: https://github.com/python/mypy/issues/15554
            filter_class(self.__dependency_provider)  # type: ignore[abstract]
            for filter_class in filter_classes
            if filter_class.get_stage() == stage
        ]
