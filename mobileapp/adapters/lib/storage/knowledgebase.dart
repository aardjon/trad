///
/// Definition of the knowledge base storage adapter.
///
library;

import 'dart:io';

import 'package:core/boundaries/storage/knowledgebase.dart';
import 'package:core/entities.dart';
import 'package:crosscuttings/di.dart';

import '../boundaries/repositories.dart';

/// Implementation of the storage adapter used by the core to interact with the knowledge base
/// repository.
class KnowledgebaseStorage implements KnowledgebaseStorageBoundary {
  /// The knowledge base data repository.
  final BlobRepositoryBoundary _repository;

  /// The ID of the knowledge base "home" document.
  static const _knowledgebaseHomeId = "/knowledgebase/index";

  /// Constructor for using the given [dependencyProvider] to obtain dependencies from other rings.
  KnowledgebaseStorage(DependencyProvider dependencyProvider)
      : _repository = dependencyProvider.provide<BlobRepositoryBoundary>();

  @override
  KnowledgebaseDocumentId getHomeIdentifier() {
    return _knowledgebaseHomeId;
  }

  @override
  KnowledgebaseDocument loadDocument(KnowledgebaseDocumentId identifier) {
    List<String> blob = _repository.loadStringContent(identifier);
    String title = _extractDocumentTitle(blob);
    String content = _extractDocumentBody(blob);
    return KnowledgebaseDocument(identifier, title, content);
  }

  /// Extracts the document title from the given [blobData].
  ///
  /// [blobData] is a multiline Markdown string (one line per list item) containing the document
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
  /// [blobData] is a multiline Markdown string (one line per list item). This method simply omits
  /// the first line (i.e. the document title) and joins all other lines into a single string, using
  /// the platform specific newline character.
  String _extractDocumentBody(List<String> blobData) {
    return blobData.sublist(1).join(Platform.lineTerminator).trimLeft();
  }
}
