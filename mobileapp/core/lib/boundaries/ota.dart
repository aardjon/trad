///
/// Definition of the core -> adapters boundary for downloading new route databases.
///
library;

/// Interface for fetching new route database versions and for checking their availability.
///
/// The actual installation is done by the RouteDbStorageBoundary.
abstract interface class RouteDbDownloadBoundary {
  /// Retrieve a list of all available route databases from the online service that are compatible
  /// with the currently running application version. The returned list is empty e.g. if there are
  /// no (compatible) databases at all. Raises in case of network errors.
  Future<List<RouteDbUpdateCandidate>> getAvailableUpdateCandidates();

  /// Download the route database with the given [identifier], write it into some temporary file and
  /// return the file path. Raises in case of network errors.
  /// The downloaded file can be deleted by calling [cleanupResources()].
  Future<String> downloadRouteDatabase(RouteDatabaseId identifier);

  /// Deletes all allocated resources like e.g. temporary files created by [downloadRouteDatabase()]
  /// calls. Should be called once at the end of an update use case.
  Future<void> cleanupResources();
}

/// ID for uniquely identifying a single route database. Not meant to be shown to users.
///
/// The exact value is undetermined and depends on the concrete implementation. The only operations
/// that are guaranteed on IDs are:
///  - Compare for (in)equality
///  - Convert to String (e.g. for printing/logging)
typedef RouteDatabaseId = String;

/// Definition of 'how compatible' a certain database is to the currently running application. This
/// is determined by some kind of format or schema version. In all cases the database is considered
/// compatible, i.e. should work without problems.
enum CompatibilityMode {
  /// The database format version is the same as required by the application.
  exactMatch,

  /// The database format is of a newer version which reports to be backward compatible to the one
  /// required by the application. This candidate may e.g. contain additional data which this
  /// application simply doesn't use.
  backwardCompatible,
}

/// Represents a single route database that can replace the current one (if any). If there are
/// several update candidates, the application has to choose from them based on the meta data
/// provided by this class.
class RouteDbUpdateCandidate {
  /// Unique identifier of this database, needed for actually downloading it.
  RouteDatabaseId identifier;

  /// The time this database was created: Newer date = more current database.
  DateTime creationDate;

  /// The compatibility level of this database.
  CompatibilityMode compatibilityMode;

  /// Constructor for directly initializing all members.
  RouteDbUpdateCandidate({
    required this.identifier,
    required this.creationDate,
    required this.compatibilityMode,
  });
}
