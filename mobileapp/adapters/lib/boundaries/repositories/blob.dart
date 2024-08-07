///
/// Definition of the boundary between storage adapters (`adapters` ring) and a concrete repository
/// implementation (`infrastructure` ring).
///
library;

/// Boundary interface to a repository storing BLOB data.
///
/// *BLOB data* means larger data like text documents or images, for example. Besides the actual
/// BLOB data, this repository also provides some meta information of the stored BLOBs, for example
/// the ID of a BLOB representing a global index/TOC for stored documents. It is a read-only
/// repository.
///
/// BLOBs are organized into namespaces, each of which can contain certain content types or
/// data of a certain application domain, for example.
abstract interface class BlobRepositoryBoundary {
  /// Returns the list of all available namespaces.
  List<BlobNamespace> getAllNamespaces();

  /// Returns the ID of the BLOB representing the index/TOC for the requested namespace.
  BlobId getIndexBlobId(BlobNamespace namespace);

  /// Retrieves and returns the content of the BLOB identified by [id] as a list of strings.
  ///
  /// Each list item represents a single line of the BLOB content (in case of a multi line string).
  /// The first and the last line are never empty.
  Future<List<String>> loadStringContent(BlobId id);
}

/// Unique name of a namespace. Each BLOB is assigned to exactly one namespace.
typedef BlobNamespace = String;

/// Unique identifier of a single BLOB.
typedef BlobId = String;
