///
/// Definition of the ApplicationWideUseCases use case class.
///
library;

import 'package:crosscuttings/di.dart';

import '../boundaries/presentation.dart';

/// General, application-wide use cases that are not specific to a certain domain.
class ApplicationWideUseCases {
  /// Interface to the presentation boundary component, used for displaying things.
  final PresentationBoundary _presentationBoundary;

  ApplicationWideUseCases(DependencyProvider di)
      : _presentationBoundary = di.provide<PresentationBoundary>();

  /// Use case of starting the trad application as a whole.
  ///
  /// This is the main use case ("entry point") for the app and is usually run exactly once during
  /// startup, after all initialization is done.
  void startApplication() {
    // Initialize the UI and immediately switch to the journal domain
    _presentationBoundary.initUserInterface();
    switchToJournal();
  }

  /// Change the active domain to the "Route Database" domain.
  void switchToRouteDb() {
    _presentationBoundary.switchToRouteDb();
  }

  /// Change the active domain to the "Journal" domain.
  void switchToJournal() {
    _presentationBoundary.switchToJournal();
  }

  /// Change the active domain to the "Knowledgebase" domain.
  void switchToKnowledgebase() {
    _presentationBoundary.switchToKnowledgebase();
  }

  /// Change the active domain to the "About" domain.
  void switchToAbout() {
    _presentationBoundary.switchToAbout();
  }
}
