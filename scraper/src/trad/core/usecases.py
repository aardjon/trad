"""
The scraper use case implementations.
"""

from logging import getLogger

from trad.core.boundaries.filters import FilterRegistry, FilterStage
from trad.crosscuttings.di import DependencyProvider

_logger = getLogger(__name__)


class ScraperUseCases:
    """
    Implementations of the main scraper use case (i.e. creating a new route data base).
    """

    def __init__(self, dependency_provider: DependencyProvider):
        """
        Create a new instance using the provided [dependency_provider] for getting dependencies.
        """
        self.__filter_registry = dependency_provider.provide(FilterRegistry)

    def produce_routedb(self) -> None:
        """
        The normal/main use case of the scraper application. Creates a new route database from
        freshly retrieved external data.
        """
        _logger.info("Now running usecase 'produce_routedb'")
        for stage in FilterStage:
            self.__run_filters_of_stage(stage)

    def __run_filters_of_stage(self, stage: FilterStage) -> None:
        """
        Executes all filters of a single stage.
        """
        filters = self.__filter_registry.get_filters(stage)
        _logger.info("Executing %i filters for stage %s", len(filters), stage.name)
        # For now, run them sequentially. To improve performance, running in parallel may be an
        # option in the future.
        for current_filter in filters:
            current_filter.execute_filter()
