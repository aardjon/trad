"""
Implementation of the PipeFactory component.
"""

from typing import override

from trad.adapters.boundaries.database import RelationalDatabaseBoundary
from trad.core.boundaries.pipes import Pipe, PipeFactory
from trad.core.boundaries.settings import SettingsBoundary
from trad.crosscuttings.di import DependencyProvider
from trad.pipes.db_v1.pipe import DbSchemaV1Pipe


class AllPipesFactory(PipeFactory):
    """
    PipeFactory implementation that simply creates all available pipes.
    """

    def __init__(self, dependency_provider: DependencyProvider):
        """Create the factory instance."""
        self.__settings = dependency_provider.provide(SettingsBoundary)
        self.__database_boundary = dependency_provider.provide(RelationalDatabaseBoundary)

    @override
    def create_pipes(self) -> list[Pipe]:
        destination_path = self.__settings.get_output_dir()
        return [DbSchemaV1Pipe(destination_path, self.__database_boundary)]
