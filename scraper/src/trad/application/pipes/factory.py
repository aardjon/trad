"""
Implementation of the PipeFactory component.
"""

from typing import override

from trad.application.pipe import CollectedData
from trad.kernel.boundaries.pipes import Pipe, PipeFactory


class AllPipesFactory(PipeFactory):
    """
    PipeFactory implementation that simply creates all available pipes.
    """

    @override
    def create_pipe(self) -> Pipe:
        return CollectedData()
