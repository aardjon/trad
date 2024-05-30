///
/// Definition of the knowledge base controller.
///
/// Controllers connect the concrete UI implementation to the `core` (in this direction) and are
/// basically responsible for mapping UI messages to use cases, converting data as necessary.
///
/// In a way, Controllers are the counterpart of Presenters.
///
library;

import 'package:adapters/boundaries/repositories.dart';
import 'package:core/usecases/knowledgebase.dart';
import 'package:crosscuttings/di.dart';

/// Controller for transmitting knowledge base UI messages to the core.
class KnowledgebaseController {
  /// The use case object from the `core` ring.
  final KnowledgebaseUseCases _knowledgebaseUsecases = KnowledgebaseUseCases(DependencyProvider());

  /// The user requested to display the document wit ID [documentId].
  void requestShowDocument(KbRepoDocumentId documentId) {
    _knowledgebaseUsecases.showDocumentPage(documentId);
  }
}
