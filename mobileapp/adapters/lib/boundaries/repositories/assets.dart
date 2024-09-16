///
/// Definition of the boundary between storage adapters (`adapters` ring) and a concrete repository
/// implementation (`infrastructure` ring).
///
library;

/// Boundary interface to a repository storing asset data.
///
/// *Asset data* means larger BLOB data that are usually deployed together with the application and
/// cannot be modified, e.g. text documents or images. Besides the actual data, this repository also
/// provides some meta information of the stored assets, for example the ID of a special file
/// containing asset metadata. It is a read-only repository.
///
/// Assets are organized into namespaces, each of which can contain certain content types or data
/// of a certain application domain, for example.
abstract interface class AssetRepositoryBoundary {
  /// Returns the list of all available namespaces.
  List<AssetNamespace> getAllNamespaces();

  /// Returns the ID of the asset containing the metadata for the assets stored in the requested
  /// [namespace].
  AssetId getMetadataAssetId(AssetNamespace namespace);

  /// Retrieves and returns the content of the asset file identified by [id] as a list of strings.
  ///
  /// Each list item represents a single line of the file content (in case of a multi line string).
  /// The first and the last line are never empty.
  Future<List<String>> loadStringContent(AssetId id);
}

/// Unique name of a namespace. Each asset is assigned to exactly one namespace.
typedef AssetNamespace = String;

/// Unique identifier of a single asset.
typedef AssetId = String;
