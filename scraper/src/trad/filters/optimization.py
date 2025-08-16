"""
Filter implementations that are supposed to run in OPTIMIZATION stage.
"""

from logging import getLogger
from typing import override

from trad.core.boundaries.filters import Filter, FilterStage
from trad.core.boundaries.pipes import Pipe
from trad.core.boundaries.settings import SettingsBoundary
from trad.crosscuttings.di import DependencyProvider

_logger = getLogger(__name__)


class PipeOptimizingFilter(Filter):
    """
    Filter for optimizing the pipe.

    This filter does some optimization regarding e.g. size or performance to the completed database.
    It does not add any further data.
    """

    @override
    def __init__(self, dependency_provider: DependencyProvider) -> None:
        """
        Constructor.
        """
        super().__init__(dependency_provider)
        self._application_settings = dependency_provider.provide(SettingsBoundary)

    @staticmethod
    @override
    def get_stage() -> FilterStage:
        return FilterStage.OPTIMIZATION

    @override
    def get_name(self) -> str:
        return "PipeOptimization"

    @override
    def execute_filter(self, pipe: Pipe) -> None:
        _logger.debug("'%s' filter started", self.get_name())
        _logger.debug("'%s' filter finished", self.get_name())
