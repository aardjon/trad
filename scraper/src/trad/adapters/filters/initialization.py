"""
Filter implementations that are supposed to run in INITIALIZING stage.
"""

from logging import getLogger
from typing import override

from trad.adapters.filters.boundaries import RouteDbCreatingPipe
from trad.core.boundaries.filters import Filter, FilterStage
from trad.core.boundaries.settings import SettingsBoundary
from trad.crosscuttings.di import DependencyProvider

_logger = getLogger(__name__)


class PipeInitializingFilter(Filter):
    """
    Filter for initializing the pipe.

    This filter ensures that the pipe is available with the underlying storage having the necessary
    structure. It does not add any data.
    """

    def __init__(self, dependency_provider: DependencyProvider) -> None:
        """
        Constructor.
        """
        self._application_settings = dependency_provider.provide(SettingsBoundary)
        self._pipe = dependency_provider.provide(RouteDbCreatingPipe)

    @staticmethod
    @override
    def get_stage() -> FilterStage:
        return FilterStage.INITIALIZATION

    @override
    def get_name(self) -> str:
        return "PipeInitialization"

    @override
    def execute_filter(self) -> None:
        _logger.debug("'%s' filter started", self.get_name())
        output_path = self._application_settings.get_output_file()
        self._pipe.initialize_pipe(output_path)
        _logger.debug("'%s' filter finished", self.get_name())
