///
/// Library providing data types used by the knowledge base domain.
///
library;

/// Uniquely identifies a single document within the knowledge base.
///
/// The exact value is undetermined and depends on the concrete storage implementation. The only
/// operations that are guaranteed on IDs are:
///  - Compare for (in)equality
///  - Convert to String (e.g. for printing/logging)
typedef KnowledgebaseDocumentId = String;

/// Represents a single document within the knowledge base.
class KnowledgebaseDocument {
  /// Unique ID of this document.
  final KnowledgebaseDocumentId identifier;

  /// Single line document title.
  final String title;

  /// Multi line document content.
  ///
  /// The content is formatted using Markdown, see https://github.github.com/gfm/ for specification.
  final String content;

  KnowledgebaseDocument(this.identifier, this.title, this.content);
}
