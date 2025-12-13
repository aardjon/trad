"""
The scraper use case implementations.
"""

from collections.abc import Collection
from logging import getLogger

from trad.kernel.boundaries.filters import Filter, FilterFactory
from trad.kernel.boundaries.pipes import Pipe, PipeFactory
from trad.kernel.di import DependencyProvider

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
        _logger.debug("Executing Filters in %i stages", self.__filter_factory.get_stage_count())
        for stage_idx, stage_filters in enumerate(self.__filter_factory.iter_filter_stages()):
            previous_pipe = pipe
            pipe = self.__pipe_factory.create_pipe()
            self.__run_filters_of_stage(
                stage_idx,
                stage_filters,
                input_pipe=previous_pipe,
                output_pipe=pipe,
            )

    def __run_filters_of_stage(
        self,
        stage_index: int,
        stage_filters: Collection[Filter],
        input_pipe: Pipe,
        output_pipe: Pipe,
    ) -> None:
        """
        Executes all given filters (of a single stage) on the given pipes.
        """
        _logger.info("Entered stage %i to run %i filters...", stage_index, len(stage_filters))
        # For now, run them sequentially. To improve performance, running in parallel may be an
        # option in the future.
        for current_filter in stage_filters:
            _logger.info("Executing filter '%s' (stage %i)", current_filter.get_name(), stage_index)
            current_filter.execute_filter(input_pipe, output_pipe)
            _logger.info("'%s' filter finished", current_filter.get_name())
