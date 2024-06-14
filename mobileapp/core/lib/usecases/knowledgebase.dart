///
/// Definition of the KnowledgebaseUseCases use case class.
///
library;

import 'dart:async';

import 'package:crosscuttings/di.dart';

import '../boundaries/presentation.dart';
import '../boundaries/storage/knowledgebase.dart';
import '../entities.dart';

/// Use cases of the knowledge base domain.
class KnowledgebaseUseCases {
  /// Interface to the presentation boundary component, used for displaying things.
  final PresentationBoundary _presentationBoundary;

  /// Interface to the storage boundary component, used for loading stored data.
  final KnowledgebaseStorageBoundary _storageBoundary;

  /// Constructor for creating a new KnowledgebaseUseCases instance.
  KnowledgebaseUseCases(DependencyProvider di)
      : _presentationBoundary = di.provide<PresentationBoundary>(),
        _storageBoundary = di.provide<KnowledgebaseStorageBoundary>();

  /// Use Case: Switching to the home document of the knowledge base domain.
  void showHomePage() {
    KnowledgebaseDocumentId homeId = _storageBoundary.getHomeIdentifier();
    unawaited(
      _storageBoundary.loadDocument(homeId).then(_presentationBoundary.showKnowledgebaseDocument),
    );
  }

  /// Use Case: Show the requested knowledge base document.
  void showDocumentPage(KnowledgebaseDocumentId documentId) {
    unawaited(
      _storageBoundary
          .loadDocument(documentId)
          .then(_presentationBoundary.showKnowledgebaseDocument),
    );
  }
}
