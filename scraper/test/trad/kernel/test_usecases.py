"""
Unit tests for the trad.kernel.usecases module.
"""

from collections.abc import Iterator
from unittest.mock import Mock, NonCallableMock

import pytest

from trad.kernel.boundaries.filters import Filter, FilterFactory
from trad.kernel.boundaries.pipes import Pipe, PipeFactory
from trad.kernel.di import DependencyProvider
from trad.kernel.usecases import ScraperUseCases


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

    @pytest.mark.parametrize("stage_count", [0, 1, 3, 5])
    def test_produce_routedb(
        self, stage_count: int, dependency_provider: DependencyProvider
    ) -> None:
        """
        Test the main scraper use case:
         - Are all filters executed for all stages?
         - Are the filters executed with the correct pipe (i.e. input pipe was the previous output
           one)?
        """
        mocked_filters = [[Mock(Filter)] for _ in range(stage_count)]
        mocked_filter_factory = NonCallableMock(FilterFactory)
        mocked_filter_factory.get_stage_count.return_value = stage_count
        mocked_filter_factory.iter_filter_stages.return_value = iter(mocked_filters)
        mocked_pipe_factory = NonCallableMock(PipeFactory)

        mocked_pipes = [Mock(Pipe, name=f"Pipe #{i}") for i in range(stage_count + 1)]
        mocked_pipe_factory.create_pipe.side_effect = mocked_pipes
        dependency_provider.register_singleton(FilterFactory, lambda: mocked_filter_factory)
        dependency_provider.register_singleton(PipeFactory, lambda: mocked_pipe_factory)

        usecases = ScraperUseCases(dependency_provider)
        usecases.produce_routedb()

        # Ensure that all pipes have been created
        assert mocked_pipe_factory.create_pipe.call_count == stage_count + 1

        # Ensure that all filters have been executed with the correct pipe instance
        for idx, filter_mock in enumerate(mocked_filters):
            filter_mock[0].execute_filter.assert_called_once_with(
                mocked_pipes[idx], mocked_pipes[idx + 1]
            )
