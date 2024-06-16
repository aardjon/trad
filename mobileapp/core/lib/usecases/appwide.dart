///
/// Definition of the ApplicationWideUseCases use case class.
///
library;

import 'package:crosscuttings/di.dart';
import 'package:crosscuttings/logging/logger.dart';

import '../boundaries/presentation.dart';

/// Logger to be used in this library file.
final Logger _logger = Logger("trad.core.usecases.appwide");

/// General, application-wide use cases that are not specific to a certain domain.
class ApplicationWideUseCases {
  /// Interface to the presentation boundary component, used for displaying things.
  final PresentationBoundary _presentationBoundary;

  /// Constructor.
  ///
  /// Expects a reference to the (fully configured) [DependencyProvider] to initialize all members.
  ApplicationWideUseCases(DependencyProvider di)
      : _presentationBoundary = di.provide<PresentationBoundary>();

  /// Use case of starting the trad application as a whole.
  ///
  /// This is the main use case ("entry point") for the app and is usually run exactly once during
  /// startup, after all initialization is done.
  void startApplication() {
    // Initialize the UI and immediately switch to the journal domain
    _logger.info("Running use case startApplication()");
    _presentationBoundary.initUserInterface();
    switchToJournal();
  }

  /// Change the active domain to the "Route Database" domain.
  void switchToRouteDb() {
    _logger.info("Running use case switchToRouteDb()");
    _presentationBoundary.switchToRouteDb();
  }

  /// Change the active domain to the "Journal" domain.
  void switchToJournal() {
    _logger.info("Running use case switchToJournal()");
    _presentationBoundary.switchToJournal();
  }

  /// Change the active domain to the "About" domain.
  void switchToAbout() {
    _logger.info("Running use case switchToAbout()");
    _presentationBoundary.switchToAbout();
  }
}
