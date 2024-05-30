///
/// Definition of the boundary between storage adapters (`adapters` ring) and a concrete repository
/// implementation (`infrastructure` ring).
///
library;

/// Boundary interface to the concrete implementation of the knowledge base data repository.
///
/// This read-only repository stores all knowledge base data (documents).
abstract interface class KnowledgebaseRepository {
  /// Returns the ID of the "home" document.
  KbRepoDocumentId getHomePageIdentifier();

  /// Retrieves and returns the title of the document identified by [identifier].
  String loadDocumentTitle(KbRepoDocumentId identifier);

  /// Retrieves and returns the (markdown) content of the document identified by [identifier].
  String loadDocumentContent(KbRepoDocumentId identifier);
}

/// Unique identifier of a knowledge base document within the the knowledge base repository.
typedef KbRepoDocumentId = String;
