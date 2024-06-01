///
/// Definition of the boundary between storage adapters (`adapters` ring) and a concrete repository
/// implementation (`infrastructure` ring).
///
library;

/// Boundary interface to a repository storing BLOB data.
///
/// *BLOB data* means larger data like text documents or images, for example. This is a read-only
/// repository.
abstract interface class BlobRepositoryBoundary {
  /// Retrieves and returns the content of the BLOB identified by [id] as a list of strings.
  ///
  /// Each list item represents a single line of the BLOB content (in case of a multi line string).
  /// The first and the last line are never empty.
  List<String> loadStringContent(BlobId id);
}

/// Unique identifier of a single BLOB.
typedef BlobId = String;
