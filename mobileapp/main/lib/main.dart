///
/// Main entry point which initializes and ties together all system parts and starts the
/// application.
///
library;

import 'package:adapters/boundaries/environment.dart';
import 'package:adapters/boundaries/repositories/blob.dart';
import 'package:adapters/boundaries/repositories/database.dart';
import 'package:adapters/sysenv.dart';
import 'package:adapters/boundaries/ui.dart';
import 'package:adapters/presenters.dart';
import 'package:adapters/storage/knowledgebase.dart';
import 'package:adapters/storage/routedb.dart';
import 'package:core/boundaries/presentation.dart';
import 'package:core/boundaries/storage/knowledgebase.dart';
import 'package:core/boundaries/storage/routedb.dart';
import 'package:core/boundaries/sysenv.dart';
import 'package:core/usecases/appwide.dart';
import 'package:crosscuttings/di.dart';
import 'package:crosscuttings/logging/logger.dart';
import 'package:infrastructure_flutter/path_provider.dart';
import 'package:infrastructure_flutter/repository/blobs.dart';
import 'package:infrastructure_flutter/ui.dart';
import 'package:infrastructure_vanilla/repositories/sqlite3.dart';

/// The global main entry point - The one and only :)
void main() {
  ApplicationBootstrap bootstrap = ApplicationBootstrap();
  bootstrap.boot();
}

/// The applications bootstrapping process.
///
/// An instance of this represents the startup process itself and is responsible for initializing
/// all the basic system parts like logging and DI, as well as initializing all dependencies. After
/// successful initialization, it runs the main use case.
class ApplicationBootstrap {
  /// Logger for the bootstrap process.
  final Logger _logger = Logger('trad.main');

  /// DI instance for configuring all the system parts.
  final DependencyProvider _dependencyProvider = DependencyProvider();

  /// Initializes and starts the trad application.
  void boot() {
    _initApp();
    _startApp();
    _logger.info('Application started successfully');
  }

  /// Initializes the trad application.
  void _initApp() {
    _setupLogging(); // Setup logging before anything else to allow logging as soon as possible
    _logger.info('Bootstrapping trad application');
    _setupDependencies();
  }

  /// Starts the trad application.
  void _startApp() {
    _logger.info('Starting trad application');
    ApplicationWideUseCases appUseCases = ApplicationWideUseCases(_dependencyProvider);
    appUseCases.startApplication();
  }

  /// Initializes the logging framework.
  void _setupLogging() {
    LogConfiguration logConfig = LogConfiguration();
    logConfig.globalLevel = LogLevel.info;
    logConfig.destination = ConsoleLogDestination();
    // TODO(aardjon): For logging to a file, use
    //  logConfig.destination = FileLogDestination("/path/to/file.log");
  }

  /// Initializes the dependency injection framework.
  void _setupDependencies() {
    _logger.info('Initializing dependencies');

    // adapter components
    _dependencyProvider.registerFactory<SystemEnvironmentBoundary>(
      () => SystemEnvironment(_dependencyProvider),
    );
    _dependencyProvider.registerFactory<PresentationBoundary>(ApplicationWidePresenter.new);
    _dependencyProvider.registerFactory<ApplicationUiBoundary>(ApplicationUI.new);
    _dependencyProvider.registerFactory<KnowledgebaseStorageBoundary>(
      () => KnowledgebaseStorage(_dependencyProvider),
    );
    _dependencyProvider.registerFactory<RouteDbStorageBoundary>(
      () => RouteDbStorage(_dependencyProvider),
    );

    // infrastructure components
    _dependencyProvider.registerFactory<PathProviderBoundary>(SystemPathProvider.new);
    _dependencyProvider.registerFactory<BlobRepositoryBoundary>(AssetRepository.new);
    _dependencyProvider.registerSingleton<RelationalDatabaseBoundary>(Sqlite3Database.new);
  }
}
