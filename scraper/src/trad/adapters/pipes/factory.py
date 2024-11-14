"""
Implementation of the PipeFactory component.
"""

from typing import override

from trad.adapters.pipes.dbschema_v1 import DbSchemaV1Pipe
from trad.core.boundaries.pipes import Pipe, PipeFactory
from trad.core.boundaries.settings import SettingsBoundary
from trad.crosscuttings.di import DependencyProvider


class AllPipesFactory(PipeFactory):
    """
    PipeFactory implementation that simply creates all available pipes.
    """

    def __init__(self, dependency_provider: DependencyProvider):
        """Create the factory instance."""
        self.__settings = dependency_provider.provide(SettingsBoundary)

    @override
    def create_pipes(self) -> list[Pipe]:
        destination_path = self.__settings.get_output_dir()
        return [DbSchemaV1Pipe(destination_path)]
