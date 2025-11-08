"""
Implementation of the FilterFactory component.
"""

from typing import Final, override

from trad.application.filters.finalization import PipeFinalizingFilter
from trad.application.filters.initialization import PipeInitializingFilter
from trad.application.filters.osm import OsmSummitDataFilter
from trad.application.filters.teufelsturm import TeufelsturmDataFilter
from trad.kernel.boundaries.filters import Filter, FilterFactory, FilterStage
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
        self.__dependency_provider = dependency_provider

    @override
    def create_filters(self, stage: FilterStage) -> list[Filter]:
        filter_classes: Final = [
            PipeInitializingFilter,
            OsmSummitDataFilter,
            TeufelsturmDataFilter,
            PipeFinalizingFilter,
        ]
        return [
            # Ignoring the MyPy warning "Cannot instantiate abstract class" here because it is a
            # known False Positive which will hopefully go away in some future version.
            # See also: https://github.com/python/mypy/issues/15554
            filter_class(self.__dependency_provider)  # type: ignore[abstract]
            for filter_class in filter_classes
            if filter_class.get_stage() == stage
        ]
