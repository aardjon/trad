"""
The 'main' component of the trad scraper application.

This component is the main entry point which initializes and ties together all system parts and
starts the actual application.
"""

import logging

from trad.adapters.cli import CliSettings
from trad.adapters.filters.boundaries import RouteDbCreatingPipe
from trad.adapters.filters.initialization import PipeInitializingFilter
from trad.adapters.pipes.dbschema_v1 import DbSchemaV1Pipe
from trad.core.boundaries.filters import FilterRegistry
from trad.core.boundaries.settings import SettingsBoundary
from trad.core.usecases import ScraperUseCases
from trad.crosscuttings.di import DependencyProvider
from trad.crosscuttings.logging import configure_logging

_logger = logging.getLogger(__name__)


def main() -> None:
    """
    The central/main execution entry point.
    """
    bootstrap = ApplicationBootstrap()
    bootstrap.init_application()
    bootstrap.run_application()


class ApplicationBootstrap:
    """
    The application's bootstrapping process.

    An instance of this represents the startup process itself and is responsible for initializing
    the DI, i.e. for mapping concrete implementations to all boundary interfaces. After successful
    initialization, it can run the main use case.
    """

    def __init__(self) -> None:
        """Constructor."""
        self.__dependency_provider = DependencyProvider()

    def init_application(self) -> None:
        """
        Initialize the application.
        """
        self.__configure_application()
        self.__setup_logging()
        _logger.info("Initializing the trad scraper application...")
        self.__setup_dependencies()
        self.__register_filters()

    def __configure_application(self) -> None:
        """
        Initialize the application settings component.

        This is done separately because it may influence the other initialization steps.
        """
        self.__dependency_provider.register_singleton(SettingsBoundary, CliSettings)

    def __setup_logging(self) -> None:
        settings = self.__dependency_provider.provide(SettingsBoundary)
        configure_logging(logging.DEBUG if settings.is_verbose() else logging.INFO)

    def __setup_dependencies(self) -> None:
        """
        Setup all components (dependencies).
        """
        # Initialize all [adapters] components
        self.__dependency_provider.register_singleton(RouteDbCreatingPipe, DbSchemaV1Pipe)

        # Initialize all [filters] components
        self.__dependency_provider.register_singleton(
            FilterRegistry, lambda: FilterRegistry(self.__dependency_provider)
        )

        # Initialize all [infrastructure] components

    def __register_filters(self) -> None:
        """
        Register all filters to the FilterRegistry
        """
        filter_registry = self.__dependency_provider.provide(FilterRegistry)
        filter_registry.register_filter_class(PipeInitializingFilter)

    def run_application(self) -> None:
        """
        Runs the application, must be called after init_application().
        """
        _logger.info("Running the scraper application...")
        usecase = ScraperUseCases(self.__dependency_provider)
        usecase.produce_routedb()

        _logger.info("Scraper run has finished, terminating gracefully...")
        self.__dependency_provider.shutdown()
