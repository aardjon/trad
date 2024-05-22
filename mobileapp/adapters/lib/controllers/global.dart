///
/// Definition of application-wide controllers that are not bound to a certain domain.
///
/// Controllers connect the concrete UI implementation to the `core` (in this direction) and are
/// basically responsible for mapping UI messages to use cases, converting data as necessary.
///
/// In a way, Controllers are the counterpart of Presenters.
///
library;

import 'package:core/usecases/global.dart';
import 'package:crosscuttings/di.dart';

/// Controller for transmitting UI messages to the core.
///
/// This is the general, application-wide controller. Domain specific use cases are separated into
/// more specialized classes.
class ApplicationWideController {
  /// The use case object from the `core` ring.
  final ApplicationWideUseCases _usecases =
      ApplicationWideUseCases(DependencyProvider());

  /// The user requested a switch to the Journal domain.
  void requestSwitchToJournal() {
    _usecases.switchToJournal();
  }

  /// The user requested a switch to the Knowledgebase domain.
  void requestSwitchToKnowledgebase() {
    _usecases.switchToKnowledgebase();
  }

  /// The user requested a switch to the Route DB domain.
  void requestSwitchToRouteDb() {
    _usecases.switchToRouteDb();
  }

  /// The user requested a switch to the About domain.
  void requestSwitchToAbout() {
    _usecases.switchToAbout();
  }
}
