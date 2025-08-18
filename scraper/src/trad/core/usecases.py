"""
The scraper use case implementations.
"""

from logging import getLogger

from trad.core.boundaries.filters import FilterFactory, FilterStage
from trad.core.boundaries.pipes import Pipe, PipeFactory
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
        self.__filter_factory = dependency_provider.provide(FilterFactory)
        self.__pipe_factory = dependency_provider.provide(PipeFactory)

    def produce_routedb(self) -> None:
        """
        The normal/main use case of the scraper application. Creates a new route database from
        freshly retrieved external data.
        """
        _logger.info("Now running usecase 'produce_routedb'")
        pipe = self.__pipe_factory.create_pipe()
        for stage in FilterStage:
            self.__run_filters_of_stage(
                stage,
                pipe,
            )

    def __run_filters_of_stage(self, stage: FilterStage, pipe: Pipe) -> None:
        """
        Executes all filters of a single `stage` on the given `pipe`.
        """
        filters = self.__filter_factory.create_filters(stage)
        _logger.info("Executing %i filters for stage %s", len(filters), stage.name)
        # For now, run them sequentially. To improve performance, running in parallel may be an
        # option in the future.
        for current_filter in filters:
            current_filter.execute_filter(pipe)
