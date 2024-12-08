"""
Unit tests for the trad.core.usecases module.
"""

from collections.abc import Iterator
from unittest.mock import Mock, NonCallableMock, call

import pytest

from trad.core.boundaries.filters import Filter, FilterFactory, FilterStage
from trad.core.boundaries.pipes import Pipe, PipeFactory
from trad.core.usecases import ScraperUseCases
from trad.crosscuttings.di import DependencyProvider


@pytest.fixture
def dependency_provider() -> Iterator[DependencyProvider]:
    """
    Fixture providing a virgin DependencyProvider (without any registrations), and cleans up all
    registrations after the test case.
    """
    dp = DependencyProvider()
    yield dp
    dp.shutdown()


class TestScraperUseCases:
    """
    Unit tests for the ScraperUseCases class.
    """

    def test_produce_routedb(self, dependency_provider: DependencyProvider) -> None:
        """
        Test the main scraper use case:
         - Are all filters retrieved (for all stages)?
         - Is the pipe created (once)?
         - Are all filters executed with the created pipe?
        """
        mocked_filters = [[Mock(Filter)] for _ in FilterStage]
        mocked_filter_factory = NonCallableMock(FilterFactory)
        mocked_filter_factory.create_filters.side_effect = (
            mocked_filters  # ([fm] for fm in mocked_filters)
        )
        mocked_pipe_factory = NonCallableMock(PipeFactory)
        mocked_pipe = Mock(Pipe)
        mocked_pipe_factory.create_pipes.return_value = [mocked_pipe]
        dependency_provider.register_singleton(FilterFactory, lambda: mocked_filter_factory)
        dependency_provider.register_singleton(PipeFactory, lambda: mocked_pipe_factory)

        usecases = ScraperUseCases(dependency_provider)
        usecases.produce_routedb()

        # Ensure that the pipes have been created
        mocked_pipe_factory.create_pipes.assert_called_once()

        # Ensure that all filters for all stages are retrieved
        assert mocked_filter_factory.create_filters.call_count == len(FilterStage)
        mocked_filter_factory.create_filters.assert_has_calls(
            [call(stage) for stage in FilterStage],
            any_order=False,
        )

        # Ensure that all filters have been executed with the given pipe instance
        for filter_mock in mocked_filters:
            filter_mock[0].execute_filter.assert_called_once_with(mocked_pipe)
