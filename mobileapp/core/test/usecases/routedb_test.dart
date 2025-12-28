///
/// Unit tests for the core.usecases.routedb library.
///
library;

import 'dart:io';

import 'package:core/boundaries/ota.dart';
import 'package:core/boundaries/sysenv.dart';
import 'package:core/entities/errors.dart';
import 'package:core/entities/geoposition.dart';
import 'package:mocktail/mocktail.dart';
import 'package:test/test.dart';

import 'package:core/boundaries/presentation.dart';
import 'package:core/boundaries/storage/preferences.dart';
import 'package:core/boundaries/storage/routedb.dart';
import 'package:core/entities/post.dart';
import 'package:core/entities/route.dart';
import 'package:core/entities/sorting/posts_filter_mode.dart';
import 'package:core/entities/sorting/routes_filter_mode.dart';
import 'package:core/entities/summit.dart';
import 'package:core/usecases/routedb.dart';
import 'package:crosscuttings/di.dart';

class RouteDbStorageBoundaryMock extends Mock implements RouteDbStorageBoundary {}

class RouteDbDownloadBoundaryMock extends Mock implements RouteDbDownloadBoundary {}

class PresentationBoundaryMock extends Mock implements PresentationBoundary {}

class AppPreferencesBoundaryMock extends Mock implements AppPreferencesBoundary {}

class SystemEnvironmentBoundaryMock extends Mock implements SystemEnvironmentBoundary {}

/// Unit tests for the core.usecases.routedb.RouteDbUseCases component.
void main() {
  setUpAll(() {
    // Register default objects which are used by mocktails `any` matcher
    registerFallbackValue(RoutesFilterMode.name);
    registerFallbackValue(PostsFilterMode.newestFirst);
    registerFallbackValue(GeoPosition(0, 0));
  });

  final DependencyProvider di = DependencyProvider();
  final RouteDbStorageBoundaryMock storageBoundaryMock = RouteDbStorageBoundaryMock();
  final RouteDbDownloadBoundaryMock downloadBoundaryMock = RouteDbDownloadBoundaryMock();
  final PresentationBoundaryMock presentationBoundaryMock = PresentationBoundaryMock();
  final AppPreferencesBoundaryMock preferencesBoundaryMock = AppPreferencesBoundaryMock();
  final SystemEnvironmentBoundaryMock systemEnvBoundaryMock = SystemEnvironmentBoundaryMock();

  setUp(() {
    // Configure DI to provide the boundary mocks
    di.registerFactory<PresentationBoundary>(() => presentationBoundaryMock);
    di.registerFactory<AppPreferencesBoundary>(() => preferencesBoundaryMock);
    di.registerFactory<SystemEnvironmentBoundary>(() => systemEnvBoundaryMock);
  });

  tearDown(() async {
    // Reset the mocks after each test case
    reset(storageBoundaryMock);
    reset(downloadBoundaryMock);
    reset(presentationBoundaryMock);
    reset(preferencesBoundaryMock);
    reset(systemEnvBoundaryMock);
    await di.shutdown();
  });

  // Tests for the route storage management (e.g. importing a new DB file)
  group('core.usecases.routedb.management', () {
    /// Dummy file path of the route database file to import
    const String fakeFilePath = 'new_route_db.sqlite';

    /// Simple happy-path test of the whole importRouteDbFile() use case: A given database file must
    /// be installed successfully.
    test('importRouteDbFile use case', () async {
      final DateTime fakeCreationDate = DateTime(2024, 8, 13);

      di.registerFactory<RouteDbStorageBoundary>(() => storageBoundaryMock);
      di.registerFactory<RouteDbDownloadBoundary>(() => downloadBoundaryMock);

      // Setup the storage mock as if everything went well
      when(storageBoundaryMock.isStarted).thenReturn(false);
      when(() => storageBoundaryMock.importRouteDbFile(any())).thenAnswer((_) async {});
      when(storageBoundaryMock.startStorage).thenAnswer((_) async {});
      when(storageBoundaryMock.getCreationDate).thenAnswer((_) async {
        return fakeCreationDate;
      });

      RouteDbUseCases usecases = RouteDbUseCases(di);
      await usecases.importRouteDbFile(fakeFilePath);

      // Make sure the correct file name is sent with the storage import request
      verify(() => storageBoundaryMock.importRouteDbFile(fakeFilePath)).called(1);

      // Make sure that the OTA component was not called
      verifyNever(downloadBoundaryMock.getAvailableUpdateCandidates);
    });

    /// Simple happy-path test of the whole importRouteDbFile() use case: A new database file must
    /// be downloaded and installed successfully.
    test('updateRouteDatabase() use case', () async {
      di.registerFactory<RouteDbStorageBoundary>(() => storageBoundaryMock);
      di.registerFactory<RouteDbDownloadBoundary>(() => downloadBoundaryMock);

      when(storageBoundaryMock.isStarted).thenReturn(false);
      when(() => storageBoundaryMock.importRouteDbFile(any())).thenAnswer((_) async {});
      when(storageBoundaryMock.startStorage).thenAnswer((_) async {});
      when(storageBoundaryMock.getCreationDate).thenAnswer((_) async {
        return DateTime(2023, 12, 25);
      });
      when(downloadBoundaryMock.getAvailableUpdateCandidates).thenAnswer((_) async {
        return <RouteDbUpdateCandidate>[
          RouteDbUpdateCandidate(
            identifier: 'db_id',
            creationDate: DateTime(2025, 1, 1),
            compatibilityMode: CompatibilityMode.exactMatch,
          ),
        ];
      });
      when(() => downloadBoundaryMock.downloadRouteDatabase(any())).thenAnswer((_) async {
        return fakeFilePath;
      });
      when(downloadBoundaryMock.cleanupResources).thenAnswer((_) async {});

      RouteDbUseCases usecases = RouteDbUseCases(di);
      await usecases.updateRouteDatabase();

      // Make sure the file name of the downloaded file was sent with the storage import request
      verify(() => storageBoundaryMock.importRouteDbFile(fakeFilePath)).called(1);

      // Make sure all created (temporary) files are deleted again
      verify(downloadBoundaryMock.cleanupResources).called(1);
    });

    // Tests for downloading database updates.
    group('download db update', () {
      // Ensures that the correct update candidate is chosen among many of them. In this test, there
      // is always a candidate to choose at the end.
      //
      // - All updates older than the currently loaded DB (if any) are completely ignored
      // - If there is only one candidate, choose it
      // - From several "exact match" candidates, choose the newest one
      // - From several candidates of the same date, prefer "exact match" over "backward compatible"
      // - Newest date is more important that "exact match" compatibility
      //
      // Test case parameters:
      //  1: Creation date of the currently started storage. Null if no storage shall be started.
      //  2: List of available updates that are returned from the RouteDbDownloadBoundary. Each item
      //     is a pair of compatibility mode (1) and creation date (2) of a single update candidate.
      //  3: Index of the update list (parameter 2) item which is expected to be chosen.
      List<(DateTime?, List<(CompatibilityMode, DateTime)>, int)> testParams =
          <(DateTime?, List<(CompatibilityMode, DateTime)>, int)>[
            (
              // Only one update candidate at all
              null,
              <(CompatibilityMode, DateTime)>[(CompatibilityMode.exactMatch, DateTime(2025, 1, 1))],
              0,
            ),

            (
              // Several candidates of the same schema version
              null,
              <(CompatibilityMode, DateTime)>[
                (CompatibilityMode.exactMatch, DateTime(2025, 1, 2)),
                (CompatibilityMode.exactMatch, DateTime(2025, 1, 3)),
                (CompatibilityMode.exactMatch, DateTime(2025, 1, 1)),
              ],
              1,
            ),

            (
              // Several candidates of the same date
              null,
              <(CompatibilityMode, DateTime)>[
                (CompatibilityMode.backwardCompatible, DateTime(2025, 1, 2)),
                (
                  CompatibilityMode.exactMatch,
                  DateTime(2025, 1, 2),
                ),
              ],
              1,
            ),

            (
              // Prefer newer candidate over exact schema version
              null,
              <(CompatibilityMode, DateTime)>[
                (CompatibilityMode.backwardCompatible, DateTime(2025, 1, 3)),
                (CompatibilityMode.exactMatch, DateTime(2025, 1, 2)),
              ],
              0,
            ),

            (
              // Ignore updates older than the currently loaded DB
              DateTime(2025, 1, 3),
              <(CompatibilityMode, DateTime)>[
                (CompatibilityMode.exactMatch, DateTime(2025, 1, 2)),
                (CompatibilityMode.backwardCompatible, DateTime(2025, 1, 4)),
              ],
              1,
            ),

            (
              // Choose the best candidate from several newer one as usual
              DateTime(2025, 1, 2),
              <(CompatibilityMode, DateTime)>[
                (CompatibilityMode.exactMatch, DateTime(2025, 1, 4)),
                (CompatibilityMode.exactMatch, DateTime(2025, 1, 1)),
                (CompatibilityMode.backwardCompatible, DateTime(2025, 1, 4)),
              ],
              0,
            ),
          ];
      for (final (DateTime?, List<(CompatibilityMode, DateTime)>, int) params in testParams) {
        test('choose candidate', () async {
          List<RouteDbUpdateCandidate> candidates = <RouteDbUpdateCandidate>[];
          params.$2.asMap().forEach((int idx, (CompatibilityMode, DateTime) candidateData) {
            candidates.add(
              RouteDbUpdateCandidate(
                identifier: 'db$idx',
                creationDate: candidateData.$2,
                compatibilityMode: candidateData.$1,
              ),
            );
          });
          di.registerFactory<RouteDbStorageBoundary>(() => _FakeStorageBoundary(params.$1));
          di.registerFactory<RouteDbDownloadBoundary>(
            () => _FakeRouteDbDownloadBoundary(
              candidates,
            ),
          );
          _DbFileInstallerMock mockedDbInstaller = _DbFileInstallerMock();
          when(() => mockedDbInstaller.installFromLocalFile(any())).thenAnswer((_) async {});

          RouteDbUseCases usecases = RouteDbUseCases(
            di,
            dbInstallerFactory: (RouteDbStorageBoundary p_, PresentationBoundary s_) =>
                mockedDbInstaller,
          );
          await usecases.updateRouteDatabase();

          String expectedDbFile = '${candidates[params.$3].identifier}.sqlite';
          verify(() => mockedDbInstaller.installFromLocalFile(expectedDbFile)).called(1);
        });
      }

      /// Ensures the correct behaviour in case all update checks went fine (i.e. no errors!), but
      /// there are no usable candidates.
      List<(DateTime?, List<(CompatibilityMode, DateTime)>)> testParameters =
          <(DateTime?, List<(CompatibilityMode, DateTime)>)>[
            (
              // Only available candidate is outdated
              DateTime(2025, 1, 5),
              <(CompatibilityMode, DateTime)>[(CompatibilityMode.exactMatch, DateTime(2025, 1, 1))],
            ),
            (
              // All available candidates are outdated
              DateTime(2025, 1, 5),
              <(CompatibilityMode, DateTime)>[
                (CompatibilityMode.backwardCompatible, DateTime(2025, 1, 3)),
                (CompatibilityMode.exactMatch, DateTime(2025, 1, 2)),
              ],
            ),
            (
              // No online updates are available at all, but storage is available
              DateTime(2025, 1, 5),
              <(CompatibilityMode, DateTime)>[],
            ),
            (
              // No online updates are available at all, and no storage is available
              null,
              <(CompatibilityMode, DateTime)>[],
            ),
          ];
      for (final (DateTime?, List<(CompatibilityMode, DateTime)>) params in testParameters) {
        test('no updates available', () async {
          List<RouteDbUpdateCandidate> candidates = <RouteDbUpdateCandidate>[];
          for (final (CompatibilityMode, DateTime) candidateData in params.$2) {
            candidates.add(
              RouteDbUpdateCandidate(
                identifier: 'db_id',
                creationDate: candidateData.$2,
                compatibilityMode: candidateData.$1,
              ),
            );
          }
          _FakeRouteDbDownloadBoundary fakeDownloader = _FakeRouteDbDownloadBoundary(
            candidates,
          );
          _FakeStorageBoundary fakeStorage = _FakeStorageBoundary(params.$1);
          di.registerFactory<RouteDbStorageBoundary>(() => fakeStorage);
          di.registerFactory<RouteDbDownloadBoundary>(() => fakeDownloader);

          _DbFileInstallerMock mockedDbInstaller = _DbFileInstallerMock();
          when(() => mockedDbInstaller.installFromLocalFile(any())).thenAnswer((_) async {});

          RouteDbUseCases usecases = RouteDbUseCases(
            di,
            dbInstallerFactory: (RouteDbStorageBoundary p_, PresentationBoundary s_) =>
                mockedDbInstaller,
          );
          await usecases.updateRouteDatabase();
          verifyNever(() => mockedDbInstaller.installFromLocalFile(any()));
        });
      }
    });

    // Tests for the LocalDbFileInstaller class.
    group('install given file', () {
      setUp(() {
        // Configure DI to provide the boundary mocks
        di.registerFactory<RouteDbStorageBoundary>(() => storageBoundaryMock);
        di.registerFactory<RouteDbDownloadBoundary>(() => downloadBoundaryMock);
      });

      /// Checks the regular, normal route DB import behaviour:
      ///  - The given file name is forwarded to the storage
      ///  - After successful import, the new storage creation date is sent to the UI
      ///  - If the storage was started before, it is stopped first (skipped if not started)
      for (final bool stopStorageFirst in <bool>[false, true]) {
        test('installFromLocalFile() success, stop first: $stopStorageFirst', () async {
          final DateTime fakeCreationDate = DateTime(2025, 7, 23);

          // Setup the storage mock as if everything went well
          when(storageBoundaryMock.isStarted).thenReturn(stopStorageFirst);
          when(() => storageBoundaryMock.importRouteDbFile(any())).thenAnswer((_) async {});
          when(storageBoundaryMock.startStorage).thenAnswer((_) async {});
          when(storageBoundaryMock.getCreationDate).thenAnswer((_) async {
            return fakeCreationDate;
          });

          LocalDbFileInstaller installer = LocalDbFileInstaller(
            di.provide<RouteDbStorageBoundary>(),
            di.provide<PresentationBoundary>(),
          );
          await installer.installFromLocalFile(fakeFilePath);

          if (stopStorageFirst) {
            // Make sure the started storage is stopped first
            verify(storageBoundaryMock.stopStorage).called(1);
          } else {
            /// Make sure the storage is not explicitly stopped first
            verifyNever(storageBoundaryMock.stopStorage);
          }
          // Make sure the correct file name is sent with the storage import request
          verify(() => storageBoundaryMock.importRouteDbFile(fakeFilePath)).called(1);
          // Make sure the storage is started (again)
          verify(storageBoundaryMock.startStorage).called(1);
          // Make sure the UI gets the storage state update and the new creation date
          verify(() => presentationBoundaryMock.updateRouteDbStatus(fakeCreationDate)).called(1);
        });
      }

      /// Ensures the correct behaviour in case some file operation failed:
      /// - The error must be handled (don't throw)
      /// - Still try to start the storage again
      /// - The UI must be notified about the storage state (with date if a previous DB can be opened)
      ///
      /// This kind of error can happen e.g. if the given file doesn't exist or is not readable.
      test('file operation error', () async {
        // Setup the storage mock to simulate an IO error during import
        when(storageBoundaryMock.isStarted).thenReturn(false);
        when(() => storageBoundaryMock.importRouteDbFile(any())).thenAnswer((_) async {
          throw const PathNotFoundException(fakeFilePath, OSError());
        });
        when(storageBoundaryMock.startStorage).thenAnswer((_) async {});
        when(storageBoundaryMock.getCreationDate).thenAnswer((_) async {
          return DateTime(2025, 9, 3);
        });

        LocalDbFileInstaller installer = LocalDbFileInstaller(
          di.provide<RouteDbStorageBoundary>(),
          di.provide<PresentationBoundary>(),
        );
        await installer.installFromLocalFile(fakeFilePath);

        // Make sure the correct file name is sent with the storage import request
        verify(() => storageBoundaryMock.importRouteDbFile(fakeFilePath)).called(1);
        // Make sure the storage is started (again)
        verify(storageBoundaryMock.startStorage).called(1);
        // Make sure the UI gets the storage state update and the creation date
        verify(() => presentationBoundaryMock.updateRouteDbStatus(any())).called(1);
      });

      /// Ensures the correct behaviour in case the new route db is invalid, e.g. missing, corrupt
      /// or just of an incompatible schema version:
      /// - The error must be handled (don't throw)
      /// - The UI must be notified about the missing storage
      for (final StorageStartingException error in <StorageStartingException>[
        InaccessibleStorageException(fakeFilePath, Exception()),
        InvalidStorageFormatException(fakeFilePath, 'Invalid file format'),
        IncompatibleStorageException(fakeFilePath, '0.1', '47.11'),
      ]) {
        test('invalid routedb error', () async {
          // Setup the storage mock to simulate an incompatible route DB file
          when(storageBoundaryMock.isStarted).thenReturn(false);
          when(() => storageBoundaryMock.importRouteDbFile(any())).thenAnswer((_) async {});
          when(storageBoundaryMock.startStorage).thenAnswer((_) async {
            throw error;
          });

          LocalDbFileInstaller installer = LocalDbFileInstaller(
            di.provide<RouteDbStorageBoundary>(),
            di.provide<PresentationBoundary>(),
          );
          await installer.installFromLocalFile(fakeFilePath);

          // Make sure the correct file name is sent with the storage import request
          verify(() => storageBoundaryMock.importRouteDbFile(fakeFilePath)).called(1);
          // Make sure the storage is started (again)
          verify(storageBoundaryMock.startStorage).called(1);
          // Make sure the UI gets the storage state update
          verify(() => presentationBoundaryMock.updateRouteDbStatus(null)).called(1);
        });
      }
    });
  });

  group('core.usecases.routedb.summits', () {
    setUp(() {
      // Configure DI to provide the boundary mocks
      di.registerFactory<RouteDbStorageBoundary>(() => storageBoundaryMock);
      di.registerFactory<RouteDbDownloadBoundary>(() => downloadBoundaryMock);
    });

    List<Summit> summitList = <Summit>[
      Summit(1, 'Mount A'),
      Summit(2, 'Mount B'),
      Summit(3, 'Mount C'),
    ];

    /// Ensures the correct behaviour of the showSummitListPage() method:
    ///  - The full summit list must be loaded from the storage (retrieveSummits())
    ///  - The retrieved list must be forwarded to the UI (updateSummitList())
    test('showSummitListPage() use case', () async {
      // Setup the storage mock
      when(() => storageBoundaryMock.retrieveSummits(any())).thenAnswer((_) async {
        return summitList;
      });

      // Run the actual test case
      RouteDbUseCases usecases = RouteDbUseCases(di);
      await usecases.showSummitListPage();

      // Make sure the full summit list (i.e. no filter string) is loaded from the storage
      verify(storageBoundaryMock.retrieveSummits).called(1);
      // Make sure the retrieved list is sent to the UI
      verify(() => presentationBoundaryMock.updateSummitList(summitList)).called(1);
    });

    /// Ensures the correct behaviour of the filterSummitList() method:
    ///  - The summit list must be loaded from the storage by providing the filter string
    ///    (retrieveSummits())
    ///  - The retrieved list must be forwarded to the UI (updateSummitList())
    test('filterSummitList() use case', () async {
      const String filterText = 'Mount';

      // Setup the storage mock
      when(() => storageBoundaryMock.retrieveSummits(any())).thenAnswer((_) async {
        return summitList;
      });

      // Run the actual test case
      RouteDbUseCases usecases = RouteDbUseCases(di);
      await usecases.filterSummitList(filterText);

      // Make sure the filter string is provided to the storage for loading the summit
      verify(() => storageBoundaryMock.retrieveSummits(filterText)).called(1);
      // Make sure the retrieved list is sent to the UI
      verify(() => presentationBoundaryMock.updateSummitList(summitList)).called(1);
    });

    /// Ensures the correct behaviour of the showSummitOnMap() method:
    ///  - The requested summit must be loaded from the storage (retrieveSummit())
    ///  - If the summit has a GeoPosition, this position is send to openExternalMapsApp()
    ///  - If the summit has no GeoPosition, nothing happens
    group('showSummitOnMap() use case', () {
      final List<Summit> testedSummits = <Summit>[
        Summit(42, 'Mount X'),
        Summit(83, 'Mount Y', GeoPosition(51.852, 13.623)),
      ];
      for (final Summit summit in testedSummits) {
        test('$summit', () async {
          // Setup the storage mock
          when(() => storageBoundaryMock.retrieveSummit(any())).thenAnswer((_) async {
            return summit;
          });
          // Setup the sysenv mock
          when(() => systemEnvBoundaryMock.openExternalMapsApp(any())).thenAnswer((_) async {});

          // Run the actual test case
          RouteDbUseCases usecases = RouteDbUseCases(di);
          await usecases.showSummitOnMap(summit.id);

          // Make sure the filter string is provided to the storage for loading the summit
          verify(() => storageBoundaryMock.retrieveSummit(summit.id)).called(1);

          // Make sure the summit's GeoPosition is provided to the SysEnv boundary (or not if
          // missing).
          if (summit.position != null) {
            verify(() => systemEnvBoundaryMock.openExternalMapsApp(summit.position!)).called(1);
          } else {
            verifyNever(() => systemEnvBoundaryMock.openExternalMapsApp(any()));
          }
        });
      }
    });
  });

  group('core.usecases.routedb.routes', () {
    setUp(() {
      // Configure DI to provide the boundary mocks
      di.registerFactory<RouteDbStorageBoundary>(() => storageBoundaryMock);
      di.registerFactory<RouteDbDownloadBoundary>(() => downloadBoundaryMock);
    });

    const RoutesFilterMode sortCriterion = RoutesFilterMode.grade;
    final Summit summit = Summit(42, 'Teufelsturm');
    final List<Route> routeList = <Route>[
      Route(1, 'Route A', 'III', 1),
      Route(2, 'Route B', 'II', 2),
      Route(3, 'Route C', 'I', 3),
    ];

    /// Ensures the correct behaviour of the showRouteListPage() method:
    ///  - The summit must be loaded from the route storage by providing its ID (retrieveSummit())
    ///  - The retrieved summit details must be sent to the UI (showSummitDetails())
    ///  - The sort criterion loaded from the preferences storage (getInitialRoutesSortCriterion())
    ///    must be provided to the routedb storage when loading the routes list
    ///    (retrieveRoutesOfSummit())
    ///  - The retrieved route list must be forwarded to the UI (updateRouteList())
    test('showRouteListPage() use case', () async {
      // Setup the storage mocks
      when(preferencesBoundaryMock.getInitialRoutesSortCriterion).thenAnswer((_) async {
        return sortCriterion; // The preferences storage provides the [sortCriterion]
      });
      when(() => storageBoundaryMock.retrieveSummit(any())).thenAnswer((_) async {
        return summit;
      });
      when(() => storageBoundaryMock.retrieveRoutesOfSummit(any(), any())).thenAnswer((_) async {
        return routeList;
      });

      // Run the actual test case
      RouteDbUseCases usecases = RouteDbUseCases(di);
      await usecases.showRouteListPage(summit.id);

      // Make sure the summit data is retrieved from the routedb storage by providing the given ID
      verify(() => storageBoundaryMock.retrieveSummit(summit.id)).called(1);
      // Make sure the summit data is sent to the UI
      verify(() => presentationBoundaryMock.showSummitDetails(summit)).called(1);
      // Make sure the sorted route list is loaded from the routedb storage, providing the correct
      // summit ID and sort criterion
      verify(() => storageBoundaryMock.retrieveRoutesOfSummit(summit.id, sortCriterion)).called(1);
      // Make sure the retrieved route list and the correct sort criterion are sent to the UI
      verify(() => presentationBoundaryMock.updateRouteList(routeList, sortCriterion)).called(1);
    });

    /// Ensures the correct behaviour of the sortRouteList() method:
    ///  - The provided sort criterion must be stored into the preferences storage
    ///    (setInitialRoutesSortCriterion())
    ///  - The given sort criterion must be provided to the routedb storage when loading the routes
    ///    (retrieveRoutesOfSummit())
    ///  - The sorted route list provided by the storage must be sent to the UI (updateRouteList())
    test('sortRouteList() use case', () async {
      // Setup the storage mocks
      when(
        () => preferencesBoundaryMock.setInitialRoutesSortCriterion(any()),
      ).thenAnswer((_) async {});
      when(() => storageBoundaryMock.retrieveRoutesOfSummit(any(), any())).thenAnswer((_) async {
        return routeList;
      });

      // Run the actual test case
      RouteDbUseCases usecases = RouteDbUseCases(di);
      await usecases.sortRouteList(summit.id, sortCriterion);

      // Make sure the sort criterion is stored in the preferences
      verify(() => preferencesBoundaryMock.setInitialRoutesSortCriterion(sortCriterion)).called(1);
      // Make sure the sorted route list is loaded from the routedb storage, providing the correct
      // summit ID and sort criterion
      verify(() => storageBoundaryMock.retrieveRoutesOfSummit(summit.id, sortCriterion)).called(1);
      // Make sure the retrieved route list and the correct sort criterion are sent to the UI
      verify(() => presentationBoundaryMock.updateRouteList(routeList, sortCriterion)).called(1);
    });
  });

  group('core.usecases.routedb.posts', () {
    setUp(() {
      // Configure DI to provide the boundary mocks
      di.registerFactory<RouteDbStorageBoundary>(() => storageBoundaryMock);
      di.registerFactory<RouteDbDownloadBoundary>(() => downloadBoundaryMock);
    });

    const PostsFilterMode sortCriterion = PostsFilterMode.oldestFirst;
    final Route route = Route(1337, 'Wanderweg', 'II', 1);
    final List<Post> postList = <Post>[
      Post('User 1', DateTime(2020), 'First Comment', 1),
      Post('User 2', DateTime(2021), 'Second Comment', 2),
      Post('User 3', DateTime(2022), 'Third Comment', 3),
    ];

    /// Ensures the correct behaviour of the showPostsPage() method:
    ///  - The route must be loaded from the route storage by providing its ID (retrieveRoute())
    ///  - The retrieved route data must be sent to the UI (showRouteDetails())
    ///  - The sort criterion loaded from the preferences storage (getInitialPostsSortCriterion())
    ///    must be provided to the routedb storage when loading the posts list
    ///    (retrievePostsOfRoute())
    ///  - The retrieved post list must be forwarded to the UI (updatePostList())
    test('showPostsPage() use case', () async {
      // Setup the storage mocks
      when(preferencesBoundaryMock.getInitialPostsSortCriterion).thenAnswer((_) async {
        return sortCriterion; // The preferences storage provides the [sortCriterion]
      });
      when(() => storageBoundaryMock.retrieveRoute(any())).thenAnswer((_) async {
        return route;
      });
      when(() => storageBoundaryMock.retrievePostsOfRoute(any(), any())).thenAnswer((_) async {
        return postList;
      });

      // Run the actual test case
      RouteDbUseCases usecases = RouteDbUseCases(di);
      await usecases.showPostsPage(route.id);

      // Make sure the route data is retrieved from the routedb storage by providing the given ID
      verify(() => storageBoundaryMock.retrieveRoute(route.id)).called(1);
      // Make sure the route data is sent to the UI
      verify(() => presentationBoundaryMock.showRouteDetails(route)).called(1);
      // Make sure the sorted post list is loaded from the routedb storage, providing the correct
      // route ID and sort criterion
      verify(() => storageBoundaryMock.retrievePostsOfRoute(route.id, sortCriterion)).called(1);
      // Make sure the retrieved route list and the correct sort criterion are sent to the UI
      verify(() => presentationBoundaryMock.updatePostList(postList, sortCriterion)).called(1);
    });

    /// Ensures the correct behaviour of the sortPostList() method:
    ///  - The provided sort criterion must be stored into the preferences storage
    ///    (setInitialPostsSortCriterion())
    ///  - The given sort criterion must be provided to the routedb storage when loading the routes
    //     (retrievePostsOfRoute())
    ///  - The sorted post list provided by the storage must be sent to the UI (updateRouteList())
    test('sortPostList() use case', () async {
      // Setup the storage mocks
      when(
        () => preferencesBoundaryMock.setInitialPostsSortCriterion(any()),
      ).thenAnswer((_) async {});
      when(() => storageBoundaryMock.retrievePostsOfRoute(any(), any())).thenAnswer((_) async {
        return postList;
      });

      // Run the actual test case
      RouteDbUseCases usecases = RouteDbUseCases(di);
      await usecases.sortPostList(route.id, sortCriterion);

      // Make sure the sort criterion is stored in the preferences
      verify(() => preferencesBoundaryMock.setInitialPostsSortCriterion(sortCriterion)).called(1);
      // Make sure the sorted route list is loaded from the routedb storage, providing the correct
      // summit ID and sort criterion
      verify(() => storageBoundaryMock.retrievePostsOfRoute(route.id, sortCriterion)).called(1);
      // Make sure the retrieved route list and the correct sort criterion are sent to the UI
      verify(() => presentationBoundaryMock.updatePostList(postList, sortCriterion)).called(1);
    });
  });
}

class _FakeStorageBoundary extends Fake implements RouteDbStorageBoundary {
  /// Creation date of teh currently started storage; null if no storage is started at all.
  final DateTime? _currentDbCreationDate;

  _FakeStorageBoundary(this._currentDbCreationDate);

  @override
  bool isStarted() {
    return _currentDbCreationDate != null;
  }

  @override
  Future<DateTime> getCreationDate() async {
    if (_currentDbCreationDate == null) {
      throw StateError('Storage not started');
    }
    return _currentDbCreationDate;
  }
}

class _FakeRouteDbDownloadBoundary extends Fake implements RouteDbDownloadBoundary {
  /// The list of candidates to be returned from getAvailableUpdateCandidates().
  final Map<RouteDatabaseId, RouteDbUpdateCandidate> _updateCandidates;

  _FakeRouteDbDownloadBoundary(List<RouteDbUpdateCandidate> updateCandidates)
    : _updateCandidates = <RouteDatabaseId, RouteDbUpdateCandidate>{
        for (RouteDbUpdateCandidate c in updateCandidates) c.identifier: c,
      };

  @override
  Future<List<RouteDbUpdateCandidate>> getAvailableUpdateCandidates() async {
    return List<RouteDbUpdateCandidate>.from(_updateCandidates.values);
  }

  @override
  Future<String> downloadRouteDatabase(RouteDatabaseId identifier) async {
    return '${_updateCandidates[identifier]!.identifier}.sqlite';
  }

  @override
  Future<void> cleanupResources() async {}
}

class _DbFileInstallerMock extends Mock implements DbFileInstaller {}
