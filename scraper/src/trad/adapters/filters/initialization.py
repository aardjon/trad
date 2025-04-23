"""
Filter implementations that are supposed to run in INITIALIZING stage.
"""

from logging import getLogger
from typing import override

from trad.core.boundaries.filters import Filter, FilterStage
from trad.core.boundaries.pipes import Pipe
from trad.core.boundaries.settings import SettingsBoundary
from trad.crosscuttings.di import DependencyProvider

_logger = getLogger(__name__)


class PipeInitializingFilter(Filter):
    """
    Filter for initializing the pipe.

    This filter ensures that the pipe is available with the underlying storage having the necessary
    structure. It does not add any data.
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
        return FilterStage.INITIALIZATION

    @override
    def get_name(self) -> str:
        return "PipeInitialization"

    @override
    def execute_filter(self, pipe: Pipe) -> None:
        _logger.debug("'%s' filter started", self.get_name())
        pipe.initialize_pipe()
        _logger.debug("'%s' filter finished", self.get_name())
