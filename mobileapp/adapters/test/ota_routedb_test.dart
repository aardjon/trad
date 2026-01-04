///
/// Unit tests for the adapters.onlineupdate library.
///
library;

import 'dart:io';
import 'dart:typed_data';

import 'package:adapters/boundaries/network.dart';
import 'package:adapters/boundaries/paths.dart';
import 'package:adapters/boundaries/repositories/filesystem.dart';
import 'package:adapters/ota_routedb.dart';
import 'package:adapters/src/storage/routedb/schema.dart';
import 'package:core/boundaries/ota.dart';
import 'package:crosscuttings/di.dart';
import 'package:mocktail/mocktail.dart';
import 'package:test/test.dart';

/// Unit tests for the adapters.onlineupdate.RouteDbOnlineUpdater class.
void main() {
  setUpAll(() {
    registerFallbackValue(Uri.https('www.example.com'));
  });

  final DependencyProvider di = DependencyProvider();
  setUp(() {
    di.registerSingleton<PathProviderBoundary>(_FakePathProvider.new);
    di.registerSingleton<FileSystemBoundary>(_DartBasedFileSystem.new);
  });

  tearDown(() async {
    await di.shutdown();
  });

  group('getAvailableUpdateCandidates() happy paths', () {
    /// Ensure the correct functionality of getAvailableUpdateCandidates() normal behaviour:
    ///  - Only return candidates compatible with the current application version
    ///  - Return multiple update candidates
    ///  - Can also return an empty candidate list
    List<(String, String, List<RouteDbUpdateCandidate>)> testParameters =
        <(String, String, List<RouteDbUpdateCandidate>)>[
          (
            'Single, exact version',
            '''
            [
              {
                "downloadUrl": "https://www.example.com/db1.sqlite",
                "schemaVersionMajor": ${supportedSchemaVersion.major},
                "schemaVersionMinor": ${supportedSchemaVersion.minor},
                "creationDate": "2025-11-28T19:59:37.245453+00:00"
              }
            ]
            ''',
            <RouteDbUpdateCandidate>[
              RouteDbUpdateCandidate(
                identifier: 'https://www.example.com/db1.sqlite',
                creationDate: DateTime.parse('2025-11-28T19:59:37.245453+00:00'),
                compatibilityMode: CompatibilityMode.exactMatch,
              ),
            ],
          ),

          (
            'Single, backward compatible version',
            '''
            [
              {
                "downloadUrl": "https://www.example.com/db1.sqlite",
                "schemaVersionMajor": ${supportedSchemaVersion.major},
                "schemaVersionMinor": ${supportedSchemaVersion.minor + 2},
                "creationDate": "2025-11-27T18:59:37.245453+00:00"
              }
            ]
            ''',
            <RouteDbUpdateCandidate>[
              RouteDbUpdateCandidate(
                identifier: 'https://www.example.com/db1.sqlite',
                creationDate: DateTime.parse('2025-11-27T18:59:37.245453+00:00'),
                compatibilityMode: CompatibilityMode.backwardCompatible,
              ),
            ],
          ),

          (
            'Multiple candidates',
            '''
            [
              {
                "downloadUrl": "https://www.example.com/db1.sqlite",
                "schemaVersionMajor": ${supportedSchemaVersion.major},
                "schemaVersionMinor": ${supportedSchemaVersion.minor + 3},
                "creationDate": "2025-11-26T17:59:37.245453+00:00"
              },
              {
                "downloadUrl": "https://www.example.com/db2.sqlite",
                "schemaVersionMajor": ${supportedSchemaVersion.major},
                "schemaVersionMinor": ${supportedSchemaVersion.minor},
                "creationDate": "2025-11-25T16:59:37.245453+00:00"
              }
            ]
            ''',
            <RouteDbUpdateCandidate>[
              RouteDbUpdateCandidate(
                identifier: 'https://www.example.com/db1.sqlite',
                creationDate: DateTime.parse('2025-11-26T17:59:37.245453+00:00'),
                compatibilityMode: CompatibilityMode.backwardCompatible,
              ),
              RouteDbUpdateCandidate(
                identifier: 'https://www.example.com/db2.sqlite',
                creationDate: DateTime.parse('2025-11-25T16:59:37.245453+00:00'),
                compatibilityMode: CompatibilityMode.exactMatch,
              ),
            ],
          ),

          (
            'Ignore minor incompatible candidates #1',
            '''
            [
              {
                "downloadUrl": "https://www.example.com/db1.sqlite",
                "schemaVersionMajor": ${supportedSchemaVersion.major},
                "schemaVersionMinor": ${supportedSchemaVersion.minor - 1},
                "creationDate": "2025-11-24T15:59:37.245453+00:00"
              },
              {
                "downloadUrl": "https://www.example.com/db2.sqlite",
                "schemaVersionMajor": ${supportedSchemaVersion.major},
                "schemaVersionMinor": ${supportedSchemaVersion.minor},
                "creationDate": "2025-11-23T14:59:37.245453+00:00"
              }
            ]
            ''',
            <RouteDbUpdateCandidate>[
              RouteDbUpdateCandidate(
                identifier: 'https://www.example.com/db2.sqlite',
                creationDate: DateTime.parse('2025-11-23T14:59:37.245453+00:00'),
                compatibilityMode: CompatibilityMode.exactMatch,
              ),
            ],
          ),

          (
            'Ignore major incompatible candidates #2',
            '''
            [
              {
                "downloadUrl": "https://www.example.com/db3.sqlite",
                "schemaVersionMajor": ${supportedSchemaVersion.major},
                "schemaVersionMinor": ${supportedSchemaVersion.minor},
                "creationDate": "2025-11-22T13:59:37.245453+00:00"
              },
              {
                "downloadUrl": "https://www.example.com/db2.sqlite",
                "schemaVersionMajor": ${supportedSchemaVersion.major - 1},
                "schemaVersionMinor": ${supportedSchemaVersion.minor},
                "creationDate": "2025-11-21T12:59:37.245453+00:00"
              },
              {
                "downloadUrl": "https://www.example.com/db1.sqlite",
                "schemaVersionMajor": ${supportedSchemaVersion.major + 1},
                "schemaVersionMinor": ${supportedSchemaVersion.minor},
                "creationDate": "2025-11-20T11:59:37.245453+00:00"
              }
            ]
            ''',
            <RouteDbUpdateCandidate>[
              RouteDbUpdateCandidate(
                identifier: 'https://www.example.com/db3.sqlite',
                creationDate: DateTime.parse('2025-11-22T13:59:37.245453+00:00'),
                compatibilityMode: CompatibilityMode.exactMatch,
              ),
            ],
          ),

          (
            'No updates at all',
            '''
            []
            ''',
            <RouteDbUpdateCandidate>[],
          ),

          (
            'No compatible updates',
            '''
            [
              {
                "downloadUrl": "https://www.example.com/db1.sqlite",
                "schemaVersionMajor": ${supportedSchemaVersion.major},
                "schemaVersionMinor": ${supportedSchemaVersion.minor - 1},
                "creationDate": "2025-11-24T15:59:37.245453+00:00"
              },
              {
                "downloadUrl": "https://www.example.com/db1.sqlite",
                "schemaVersionMajor": ${supportedSchemaVersion.major + 1},
                "schemaVersionMinor": ${supportedSchemaVersion.minor},
                "creationDate": "2025-11-20T11:59:37.245453+00:00"
              }
             ]
            ''',
            <RouteDbUpdateCandidate>[],
          ),
        ];

    for (final (String, String, List<RouteDbUpdateCandidate>) params in testParameters) {
      String testCaseLabel = params.$1;
      test(testCaseLabel, () async {
        di.registerSingleton<HttpNetworkingBoundary>(() => _FakeNetwork(params.$2, Uint8List(0)));
        List<RouteDbUpdateCandidate> expectedCandidates = params.$3;

        RouteDbOnlineUpdater updater = RouteDbOnlineUpdater(di);
        List<RouteDbUpdateCandidate> updateCandidates = await updater
            .getAvailableUpdateCandidates();

        expect(updateCandidates.length, expectedCandidates.length);
        for (final (RouteDbUpdateCandidate, RouteDbUpdateCandidate) item
            in List<(RouteDbUpdateCandidate, RouteDbUpdateCandidate)>.generate(
              updateCandidates.length,
              (int i) => (updateCandidates[i], expectedCandidates[i]),
            )) {
          RouteDbUpdateCandidate actual = item.$1;
          RouteDbUpdateCandidate expected = item.$2;
          expect(actual.identifier, expected.identifier);
          expect(actual.compatibilityMode, expected.compatibilityMode);
          expect(actual.creationDate, expected.creationDate);
        }
      });
    }
  });

  /// Ensure the functionality of downloading route database files (downloadRouteDatabase()), and
  /// their deletion (cleanupResources()).
  ///  - The relative URL is resolved correctly
  ///  - The response binary data is written into a temporary file
  ///  - Calling cleanupResources() deletes the written file
  test('download & cleanup happy paths', () async {
    Uint8List expectedFileContent = Uint8List.fromList(<int>[47, 11, 42, 13, 37]);
    _FakeNetwork fakeNetwork = _FakeNetwork('', expectedFileContent);
    di.registerSingleton<HttpNetworkingBoundary>(() => fakeNetwork);

    RouteDbOnlineUpdater updater = RouteDbOnlineUpdater(di);
    String downloadedFilePath = await updater.downloadRouteDatabase('../dummy_db_id');

    // Make sure the adapter requested the correct URL
    Uri expectedUrl = Uri.https('www.fomori.de', 'trad/dummy_db_id');
    expect(fakeNetwork.requestedUrls.last, expectedUrl);

    // Make sure the downloaded file contains the expected data
    File dbFile = File(downloadedFilePath);
    Uint8List fileContent = await dbFile.readAsBytes();
    expect(fileContent, expectedFileContent);

    // Make sure calling cleanupResources() deletes the downloaded file
    await updater.cleanupResources();
    expect(dbFile.existsSync(), false);
  });
}

class _FakePathProvider extends Fake implements PathProviderBoundary {
  @override
  Future<Directory> getTempDir() async {
    return Directory.systemTemp.createTemp('test_ota_routedb');
  }
}

class _DartBasedFileSystem extends Fake implements FileSystemBoundary {
  @override
  File getFile(String filePath) {
    return File(filePath);
  }

  @override
  Directory getDirectory(String directoryPath) {
    return Directory(directoryPath);
  }
}

class _FakeNetwork extends Fake implements HttpNetworkingBoundary {
  /// The JSON string to be returned by retrieveJsonResource()
  final String _jsonResponse;

  // Binary data to be returned by
  final Uint8List _binaryResponse;

  List<Uri> requestedUrls = <Uri>[];

  _FakeNetwork(this._jsonResponse, this._binaryResponse);

  @override
  Future<String> retrieveJsonResource(Uri url) async {
    requestedUrls.add(url);
    return _jsonResponse;
  }

  @override
  Future<Uint8List> retrieveBinaryResource(Uri url) async {
    requestedUrls.add(url);
    return _binaryResponse;
  }
}
