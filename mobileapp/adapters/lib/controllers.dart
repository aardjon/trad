///
/// Provides controller implementations.
///
/// Controllers connect the concrete UI implementation to the `core` (in this direction) and are
/// basically responsible for mapping UI messages to use cases, converting data as necessary.
///
/// In a way, Controllers are the counterpart of Presenters.
///
library;

import 'package:core/usecases/appwide.dart';
import 'package:core/usecases/knowledgebase.dart';
import 'package:crosscuttings/di.dart';

import 'boundaries/repositories.dart';

/// Controller for transmitting UI messages to the core.
///
/// This is the general, application-wide controller. Domain specific use cases are separated into
/// more specialized classes.
class ApplicationWideController {
  /// The use case object from the `core` ring.
  final ApplicationWideUseCases _globalUsecases = ApplicationWideUseCases(DependencyProvider());

  final KnowledgebaseUseCases _knowledgebaseUsecases = KnowledgebaseUseCases(DependencyProvider());

  /// The user requested a switch to the Journal domain.
  void requestSwitchToJournal() {
    _globalUsecases.switchToJournal();
  }

  /// The user requested a switch to the knowledge base domain.
  void requestSwitchToKnowledgebase() {
    _knowledgebaseUsecases.showHomePage();
  }

  /// The user requested a switch to the Route DB domain.
  void requestSwitchToRouteDb() {
    _globalUsecases.switchToRouteDb();
  }

  /// The user requested a switch to the About domain.
  void requestSwitchToAbout() {
    _globalUsecases.switchToAbout();
  }
}

/// Controller for transmitting knowledge base UI messages to the core.
class KnowledgebaseController {
  /// The use case object from the `core` ring.
  final KnowledgebaseUseCases _knowledgebaseUsecases = KnowledgebaseUseCases(DependencyProvider());

  /// The user requested to display the document wit ID [documentId].
  void requestShowDocument(BlobId documentId) {
    _knowledgebaseUsecases.showDocumentPage(documentId);
  }
}
