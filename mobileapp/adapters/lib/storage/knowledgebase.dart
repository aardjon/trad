///
/// Definition of the knowledge base storage adapter.
///
library;

import 'package:core/boundaries/storage/knowledgebase.dart';
import 'package:core/entities/knowledgebase.dart';
import 'package:crosscuttings/di.dart';

import '../boundaries/repositories.dart';

/// Implementation of the storage adapter used by the core to interact with the knowledge base
/// repository.
class KnowledgebaseStorage implements KnowledgebaseStorageBoundary {
  /// The knowledge base data repository.
  final KnowledgebaseRepository _repository;

  /// Constructor for using the given [dependencyProvider] to obtain dependencies from other rings.
  KnowledgebaseStorage(DependencyProvider dependencyProvider)
      : _repository = dependencyProvider.provide<KnowledgebaseRepository>();

  @override
  KnowledgebaseDocumentId getHomeIdentifier() {
    return _repository.getHomePageIdentifier();
  }

  @override
  KnowledgebaseDocument loadDocument(KnowledgebaseDocumentId identifier) {
    String title = _repository.loadDocumentTitle(identifier);
    String content = _repository.loadDocumentContent(identifier);
    return KnowledgebaseDocument(identifier, title, content);
  }
}
