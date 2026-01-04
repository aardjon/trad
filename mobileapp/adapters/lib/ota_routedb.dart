///
/// Provides a component for downloading route databases using an external web service.
///
library;

import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';

import 'package:core/boundaries/ota.dart';

import 'boundaries/network.dart';
import 'package:crosscuttings/di.dart';

import 'boundaries/paths.dart';
import 'boundaries/repositories/filesystem.dart';
import 'src/storage/routedb/schema.dart';

/// OTA update implementation for download updated route DBs via the 'trad.ota' web interface.
/// This service basically provides a JSON formatted list of available route databases. This
/// component filters them for the ones that are compatible with the currently running application
/// version.
class RouteDbOnlineUpdater implements RouteDbDownloadBoundary {
  /// Interface to the component providing network access.
  final HttpNetworkingBoundary _networkBoundary;

  /// Interface to the component providing system path information.
  final PathProviderBoundary _pathProvider;

  /// Interface to the component providing file system access.
  final FileSystemBoundary _fsBoundary;

  /// List of created directories that need to be deleted at some point.
  final List<Directory> _directoriesToDelete = <Directory>[];

  /// Basic URL of the OTA web service to use
  static final Uri _otaBaseUrl = Uri.https('www.fomori.de', '/trad/ota/');
  // Full API endpoint URL of the OTA web service to use
  static final Uri _otaApiEndpoint = _otaBaseUrl.resolve('api.php');

  /// Constructor for using the given [dependencyProvider] to obtain dependencies from other rings.
  RouteDbOnlineUpdater(DependencyProvider dependencyProvider)
    : _networkBoundary = dependencyProvider.provide<HttpNetworkingBoundary>(),
      _pathProvider = dependencyProvider.provide<PathProviderBoundary>(),
      _fsBoundary = dependencyProvider.provide<FileSystemBoundary>();

  @override
  Future<List<RouteDbUpdateCandidate>> getAvailableUpdateCandidates() async {
    String jsonData = await _networkBoundary.retrieveJsonResource(_otaApiEndpoint);

    List<RouteDbUpdateCandidate> availableCandidates = <RouteDbUpdateCandidate>[];
    for (final RouteDbMetadataJson candidate in _deserializeJsonResponse(jsonData)) {
      if (_isCompatible(candidate)) {
        availableCandidates.add(_createCandidateInfo(candidate));
      }
    }
    return availableCandidates;
  }

  List<RouteDbMetadataJson> _deserializeJsonResponse(String jsonString) {
    List<dynamic> jsonMetadata = jsonDecode(jsonString) as List<dynamic>;

    return List<RouteDbMetadataJson>.from(
      jsonMetadata.map((dynamic x) => RouteDbMetadataJson.fromJson(x as Map<String, dynamic>)),
    );
  }

  bool _isCompatible(RouteDbMetadataJson candidate) {
    return candidate.schemaVersionMajor == supportedSchemaVersion.major &&
        candidate.schemaVersionMinor >= supportedSchemaVersion.minor;
  }

  RouteDbUpdateCandidate _createCandidateInfo(RouteDbMetadataJson candidate) {
    return RouteDbUpdateCandidate(
      identifier: candidate.downloadUrl,
      creationDate: candidate.creationDate,
      compatibilityMode: candidate.schemaVersionMinor == supportedSchemaVersion.minor
          ? CompatibilityMode.exactMatch
          : CompatibilityMode.backwardCompatible,
    );
  }

  @override
  Future<String> downloadRouteDatabase(RouteDatabaseId identifier) async {
    final Uri databaseUri = _otaBaseUrl.resolve(identifier);
    final Directory tempDir = await (await _pathProvider.getTempDir()).createTemp();
    _directoriesToDelete.add(tempDir);
    final File tempFile = _fsBoundary.getFile('${tempDir.path}/routedb.sqlite');

    Uint8List fileContent = await _networkBoundary.retrieveBinaryResource(databaseUri);
    await tempFile.writeAsBytes(fileContent, flush: true);
    return tempFile.path;
  }

  @override
  Future<void> cleanupResources() async {
    for (final Directory createdFile in _directoriesToDelete) {
      await createdFile.delete(recursive: true);
    }
    _directoriesToDelete.clear();
  }
}

/// Represents the JSON structured data describing a single route database, as provided by the
/// trad.ota web service.
class RouteDbMetadataJson {
  /// The URL (relative to the API endpoint) from which this route database can be downloaded.
  final String downloadUrl;

  /// Major schema version of this route database.
  final int schemaVersionMajor;

  /// Minor schema version of this route database.
  final int schemaVersionMinor;

  /// Creation time stamp of this route database.
  final DateTime creationDate;

  /// Constructor for directly initializing all members.
  RouteDbMetadataJson({
    required this.downloadUrl,
    required this.schemaVersionMajor,
    required this.schemaVersionMinor,
    required this.creationDate,
  });

  /// Creates and returns a new RouteDbMetadataJson instance from the given [jsonData] map. Raises
  /// FormatException if the JSON doesn't contain the expected data or cannot be parsed at all.
  factory RouteDbMetadataJson.fromJson(Map<String, dynamic> jsonData) {
    String url = _readJsonValue<String>(jsonData, 'downloadUrl');
    int majorVersion = _readJsonValue<int>(jsonData, 'schemaVersionMajor');
    int minorVersion = _readJsonValue<int>(jsonData, 'schemaVersionMinor');
    String creationDateStr = _readJsonValue<String>(jsonData, 'creationDate');
    DateTime? creationDate = DateTime.tryParse(creationDateStr);
    if (creationDate == null) {
      throw FormatException('Invalid creation timestamp', creationDateStr);
    }

    return RouteDbMetadataJson(
      downloadUrl: url,
      schemaVersionMajor: majorVersion,
      schemaVersionMinor: minorVersion,
      creationDate: creationDate,
    );
  }

  /// Read the value of the requested [key] from the the given [jsonData] JSON map and convert it
  /// into the destination [ValueType]. Returns the converted value, or raises FormatException if
  /// the key doesn't exist or the value cannot be converted.
  static ValueType _readJsonValue<ValueType>(Map<String, dynamic> jsonData, String key) {
    ValueType? value = jsonData[key] as ValueType?;
    if (value == null) {
      throw FormatException("Expected key '$key' is missing in JSON data", jsonData);
    }
    return value;
  }
}
