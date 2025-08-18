"""
Filter implementations that are supposed to run in FINALIZATION stage.
"""

from logging import getLogger
from typing import override

from trad.core.boundaries.filters import Filter, FilterStage
from trad.core.boundaries.pipes import Pipe
from trad.crosscuttings.di import DependencyProvider

_logger = getLogger(__name__)


class PipeFinalizingFilter(Filter):
    """
    Filter for finalizing the pipe.

    This filter ensures that the pipe data is written to the output file, and closes the pipe. It
    does not modify the data.
    """

    @override
    def __init__(self, dependency_provider: DependencyProvider) -> None:
        """
        Constructor.
        """
        super().__init__(dependency_provider)

    @staticmethod
    @override
    def get_stage() -> FilterStage:
        return FilterStage.FINALIZATION

    @override
    def get_name(self) -> str:
        return "PipeFinalization"

    @override
    def execute_filter(self, pipe: Pipe) -> None:
        _logger.debug("'%s' filter started", self.get_name())
        pipe.finalize_pipe()
        _logger.debug("'%s' filter finished", self.get_name())
