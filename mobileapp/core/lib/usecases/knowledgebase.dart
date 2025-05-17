///
/// Definition of the KnowledgebaseUseCases use case class.
///
library;

import 'dart:async';

import 'package:crosscuttings/di.dart';
import 'package:crosscuttings/logging/logger.dart';

import '../boundaries/presentation.dart';
import '../boundaries/storage/knowledgebase.dart';
import '../entities/knowledgebase.dart';

/// Logger to be used in this library file.
final Logger _logger = Logger('trad.core.usecases.knowledgebase');

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
  Future<void> showHomePage() async {
    _logger.info('Running use case showHomePage()');
    KnowledgebaseDocumentId homeId = _storageBoundary.getHomeIdentifier();
    KnowledgebaseDocument document = await _storageBoundary.loadDocument(homeId);
    _presentationBoundary.showKnowledgebaseDocument(document);
  }

  /// Use Case: Show the requested knowledge base document.
  Future<void> showDocumentPage(KnowledgebaseDocumentId documentId) async {
    _logger.info('Running use case showDocumentPage($documentId)');
    KnowledgebaseDocument document = await _storageBoundary.loadDocument(documentId);
    _presentationBoundary.showKnowledgebaseDocument(document);
  }
}
