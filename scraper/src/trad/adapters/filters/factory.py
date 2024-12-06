"""
Implementation of the FilterFactory component.
"""

from typing import override

from trad.adapters.filters.filling.teufelsturm import TeufelsturmDataFilter
from trad.adapters.filters.initialization import PipeInitializingFilter
from trad.adapters.filters.optimization import PipeOptimizingFilter
from trad.core.boundaries.filters import Filter, FilterFactory, FilterStage
from trad.crosscuttings.di import DependencyProvider


class AllFiltersFactory(FilterFactory):
    """
    The factory for creating all filters that should be executed.
    """

    def __init__(self, dependency_provider: DependencyProvider) -> None:
        """
        Create a new FilterFactory with the given [dependency_provider].
        """
        self.__filters = [
            PipeInitializingFilter(dependency_provider),
            TeufelsturmDataFilter(dependency_provider),
            PipeOptimizingFilter(dependency_provider),
        ]

    @override
    def create_filters(self, stage: FilterStage) -> list[Filter]:
        return [f for f in self.__filters if f.get_stage() == stage]
