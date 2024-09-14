///
/// Unit tests for the core.usecases.routedb library.
///
library;

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

class PresentationBoundaryMock extends Mock implements PresentationBoundary {}

class AppPreferencesBoundaryMock extends Mock implements AppPreferencesBoundary {}

/// Unit tests for the core.usecases.routedb.RouteDbUseCases component.
void main() {
  setUpAll(() {
    // Register a default document object which is used by mocktails `any` matcher
    registerFallbackValue(RoutesFilterMode.name);
    registerFallbackValue(PostsFilterMode.newestFirst);
  });

  final DependencyProvider di = DependencyProvider();
  final RouteDbStorageBoundaryMock storageBoundaryMock = RouteDbStorageBoundaryMock();
  final PresentationBoundaryMock presentationBoundaryMock = PresentationBoundaryMock();
  final AppPreferencesBoundaryMock preferencesBoundaryMock = AppPreferencesBoundaryMock();

  // Configure DI to provide the boundary mocks
  di.registerFactory<RouteDbStorageBoundary>(() => storageBoundaryMock);
  di.registerFactory<PresentationBoundary>(() => presentationBoundaryMock);
  di.registerFactory<AppPreferencesBoundary>(() => preferencesBoundaryMock);

  tearDown(() {
    // Reset the mocks after each test case
    reset(storageBoundaryMock);
    reset(presentationBoundaryMock);
    reset(preferencesBoundaryMock);
  });

  group('core.usecases.routedb.summits', () {
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
  });

  group('core.usecases.routedb.routes', () {
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
      when(() => preferencesBoundaryMock.setInitialRoutesSortCriterion(any()))
          .thenAnswer((_) async {});
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
      when(() => preferencesBoundaryMock.setInitialPostsSortCriterion(any()))
          .thenAnswer((_) async {});
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
