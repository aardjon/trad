///
/// Definition of the knowledge base storage adapter.
///
library;

import 'dart:io';

import 'package:core/boundaries/storage/knowledgebase.dart';
import 'package:core/entities.dart';
import 'package:crosscuttings/di.dart';
import 'package:crosscuttings/logging/logger.dart';

import '../boundaries/repositories.dart';

/// Logger to be used in this library file.
final Logger _logger = Logger("trad.adapters.storage.knowledgebase");

/// Implementation of the storage adapter used by the core to interact with the knowledge base
/// repository.
class KnowledgebaseStorage implements KnowledgebaseStorageBoundary {
  /// The knowledge base data repository.
  final BlobRepositoryBoundary _repository;

  /// Constructor for using the given [dependencyProvider] to obtain dependencies from other rings.
  KnowledgebaseStorage(DependencyProvider dependencyProvider)
      : _repository = dependencyProvider.provide<BlobRepositoryBoundary>();

  @override
  KnowledgebaseDocumentId getHomeIdentifier() {
    _logger.debug("Retrieving home document ID");
    BlobNamespace knowledgebaseNamespace = _repository.getAllNamespaces().firstWhere(
          (BlobNamespace element) => element.contains("knowledgebase"),
        );
    return _repository.getIndexBlobId(knowledgebaseNamespace);
  }

  @override
  Future<KnowledgebaseDocument> loadDocument(KnowledgebaseDocumentId identifier) async {
    _logger.debug("Loading document $identifier");
    List<String> blob = await _repository.loadStringContent(identifier);
    _logger.debug("Document $identifier loaded, processing");
    String title = _extractDocumentTitle(blob);
    String content = _extractDocumentBody(blob);
    _logger.debug("Processed document $identifier");
    return KnowledgebaseDocument(identifier, title, content);
  }

  /// Extracts the document title from the given [blobData].
  ///
  /// [blobData] is a multiline Markdown string (each list item is one line) containing the document
  /// title as the very first line. Any prepending Markdown annotation (e.g. '#') is removed.
  String _extractDocumentTitle(List<String> blobData) {
    String titleLine = blobData[0].trim();
    while (titleLine.startsWith("#")) {
      titleLine = titleLine.substring(1);
    }
    return titleLine.trim();
  }

  /// Extracts the document body from the given [blobData].
  ///
  /// [blobData] is a multiline Markdown string (each list item is one line). This method simply
  /// omits the first line (i.e. the document title) and joins all other lines into a single string,
  /// using the platform specific newline character.
  String _extractDocumentBody(List<String> blobData) {
    return blobData.sublist(1).join(Platform.lineTerminator).trimLeft();
  }
}
