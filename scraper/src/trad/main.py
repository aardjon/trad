"""
The 'main' component of the trad scraper application.

This component is the main entry point which initializes and ties together all system parts and
starts the actual application.
"""

import logging
from functools import partial
from typing import TYPE_CHECKING

from trad.application.adapters.boundaries.database import RelationalDatabaseBoundary
from trad.application.adapters.boundaries.http import HttpNetworkingBoundary
from trad.application.filters.factory import AllFiltersFactory
from trad.application.pipes.factory import AllPipesFactory
from trad.infrastructure.cli import CliSettings
from trad.infrastructure.http_recorder import TrafficPlayer, TrafficRecorder
from trad.infrastructure.logging import (
    configure_console_logging,
    configure_file_logging,
    configure_log_channel,
    initialize_logging,
)
from trad.infrastructure.requests import RequestsHttp
from trad.infrastructure.sqlite3db import Sqlite3Database
from trad.kernel.appmeta import APPLICATION_NAME, APPLICATION_VERSION
from trad.kernel.boundaries.filters import FilterFactory
from trad.kernel.boundaries.pipes import PipeFactory
from trad.kernel.boundaries.settings import SettingsBoundary
from trad.kernel.di import DependencyProvider
from trad.kernel.usecases import ScraperUseCases

if TYPE_CHECKING:
    from collections.abc import Callable

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
        _logger.info(
            "Initializing the %s application version %s...", APPLICATION_NAME, APPLICATION_VERSION
        )
        self.__setup_dependencies()

    def __configure_application(self) -> None:
        """
        Initialize the application settings component.

        This is done separately because it may influence the other initialization steps.
        """
        self.__dependency_provider.register_singleton(SettingsBoundary, CliSettings)

    def __setup_logging(self) -> None:
        settings = self.__dependency_provider.provide(SettingsBoundary)

        initialize_logging()
        configure_console_logging(logging.DEBUG if settings.is_verbose() else logging.INFO)
        log_file = settings.get_log_file()
        if log_file is not None:
            configure_file_logging(log_file, logging.DEBUG)

        # Disable some log channels because they are too chatty

        # The statement_creator logs all executed SQL statements on DEBUG level
        configure_log_channel("trad.infrastructure.sqlite3db.statement_creator", logging.INFO)
        # urllib3 logs every single HTTP request
        configure_log_channel("urllib3", logging.WARNING)

    def __setup_dependencies(self) -> None:
        """
        Setup all components (dependencies).
        """
        settings = self.__dependency_provider.provide(SettingsBoundary)

        # Initialize all [application] components
        self.__dependency_provider.register_factory(
            PipeFactory, lambda: AllPipesFactory(self.__dependency_provider)
        )
        self.__dependency_provider.register_factory(
            FilterFactory, lambda: AllFiltersFactory(self.__dependency_provider)
        )

        # Initialize all [infrastructure] components
        self.__dependency_provider.register_singleton(RelationalDatabaseBoundary, Sqlite3Database)

        traffic_recording_path = settings.get_traffic_recordings_path()
        network_factory: Callable[[], HttpNetworkingBoundary] = RequestsHttp
        if traffic_recording_path is not None:
            if settings.is_record_traffic_mode():
                network_factory = partial(TrafficRecorder, traffic_recording_path, RequestsHttp())
            elif settings.is_replay_traffic_mode():
                network_factory = partial(TrafficPlayer, traffic_recording_path)
        self.__dependency_provider.register_singleton(HttpNetworkingBoundary, network_factory)

    def run_application(self) -> None:
        """
        Runs the application, must be called after init_application().
        """
        _logger.info("Running the %s application...", APPLICATION_NAME)
        usecase = ScraperUseCases(self.__dependency_provider)
        usecase.produce_routedb()

        _logger.info("The %s application has finished, terminating gracefully...", APPLICATION_NAME)
        self.__dependency_provider.shutdown()
