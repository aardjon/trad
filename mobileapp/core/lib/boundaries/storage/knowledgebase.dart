///
/// Definition of the boundary between the core and the knowledge base storage.
///
library;

import '../../entities.dart';

/// Interface providing knowledge base data to the core.
///
/// The knowledge base stores a collection of text documents that can be browsed (think of a wiki).
/// Each document is uniquely identified by a [KnowledgebaseDocumentId] and (once loaded)
/// represented by a [KnowledgebaseDocument]. Besides loading documents, the storage allows to
/// retrieve the IDs of some special documents (e.g. a start/index document).
///
/// The knowledge base is a read only data storage.
abstract interface class KnowledgebaseStorageBoundary {
  /// Returns the ID of the "home" document.
  ///
  /// The home document is meant to be used be used as a starting point to the knowledge base,
  /// containing e.g. a table of contents.
  KnowledgebaseDocumentId getHomeIdentifier();

  /// Loads and returns the document with the given [documentId].
  KnowledgebaseDocument loadDocument(KnowledgebaseDocumentId documentId);
}
