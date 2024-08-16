///
/// Definition of the ApplicationWideUseCases use case class.
///
library;

import 'package:crosscuttings/di.dart';
import 'package:crosscuttings/logging/logger.dart';

import '../boundaries/presentation.dart';
import '../boundaries/storage/routedb.dart';
import '../boundaries/sysenv.dart';
import '../entities/path.dart';

/// Logger to be used in this library file.
final Logger _logger = Logger('trad.core.usecases.appwide');

/// General, application-wide use cases that are not specific to a certain domain.
class ApplicationWideUseCases {
  /// Interface to the system environment component, used to retrieve environment specific
  /// information.
  final SystemEnvironmentBoundary _sysEnvBoundary;

  /// Interface to the presentation boundary component, used for displaying things.
  final PresentationBoundary _presentationBoundary;

  /// Interface to the storage boundary component, used for obtaining data.
  final RouteDbStorageBoundary _routeDbBoundary;

  /// Constructor.
  ///
  /// Expects a reference to the (fully configured) [DependencyProvider] to initialize all members.
  ApplicationWideUseCases(DependencyProvider di)
      : _presentationBoundary = di.provide<PresentationBoundary>(),
        _routeDbBoundary = di.provide<RouteDbStorageBoundary>(),
        _sysEnvBoundary = di.provide<SystemEnvironmentBoundary>();

  /// Use case of starting the trad application as a whole.
  ///
  /// This is the main use case ("entry point") for the app and is usually run exactly once during
  /// startup, after all initialization is done.
  Future<void> startApplication() async {
    // Initialize the UI
    _logger.info('Running use case startApplication()');
    _presentationBoundary.initUserInterface();
    // Initialize the storage components
    // TODO(aardjon): Where to get the data directory path from?
    const String routesFile = '/path/to/the/routedb.sqlite';
    _routeDbBoundary.initStorage(routesFile);
    // Finally, switch to the journal domain
    switchToJournal();
  }

  /// Change the active domain to the "Journal" domain.
  void switchToJournal() {
    _logger.info('Running use case switchToJournal()');
    _presentationBoundary.switchToJournal();
  }

  /// Change the active domain to the "About" domain.
  void switchToAbout() {
    _logger.info('Running use case switchToAbout()');
    _presentationBoundary.switchToAbout();
  }
}
