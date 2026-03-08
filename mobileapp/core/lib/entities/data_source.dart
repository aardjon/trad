///
/// Definition of the [DataSourceAttribution] entity class.
///
library;

/// Represents an external source from which data is imported.
///
/// External sources are uniquely identified by their label.
class DataSourceAttribution {
  /// Display name of this data source. This name must be unique within the route DB.
  String label;

  /// Landing page URL (not an API endpoint!) a user may visit by browser to get further
  /// information about this data source.
  String url;

  /// Attribution string (e.g. author names, copyright) for the data from this source.
  String attribution;

  /// Short, human readable name of the data license, if any. None if there is no explicit license
  /// (but e.g. some individual agreement).
  String? license;

  /// Constructor for directly initializing all members.
  DataSourceAttribution({
    required this.label,
    required this.url,
    required this.attribution,
    this.license,
  });
}
