///
/// Unit tests for the core.usecases.appwide library.
///
library;

import 'package:core/boundaries/presentation.dart';
import 'package:core/boundaries/storage/preferences.dart';
import 'package:core/boundaries/storage/routedb.dart';
import 'package:core/entities/errors.dart';
import 'package:core/usecases/appwide.dart';
import 'package:crosscuttings/di.dart';
import 'package:mocktail/mocktail.dart';
import 'package:test/test.dart';

class RouteDbStorageBoundaryMock extends Mock implements RouteDbStorageBoundary {}

class PresentationBoundaryMock extends Mock implements PresentationBoundary {}

class AppPreferencesBoundaryMock extends Mock implements AppPreferencesBoundary {}

/// Unit tests for the core.usecases.appwide.ApplicationWideUseCases component.
void main() {
  setUpAll(() {
    // Register default objects which are used by mocktails `any` matcher
    /*registerFallbackValue(RoutesFilterMode.name);
    registerFallbackValue(PostsFilterMode.newestFirst);
    registerFallbackValue(GeoPosition(0, 0));*/
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

  /// Ensure that the application is fully started even without a usable route database. The only
  /// difference to the regular start is, that the UI starts on the settings page.
  test('startApplication() without routedb', () async {
    when(preferencesBoundaryMock.initStorage).thenAnswer((_) async {});
    when(storageBoundaryMock.startStorage).thenAnswer((_) async {
      throw StorageStartingException('missing_routedb');
    });

    ApplicationWideUseCases usecases = ApplicationWideUseCases(di);
    await usecases.startApplication();

    // Make sure that all components (UI, preferences) have been initialized
    verify(presentationBoundaryMock.initUserInterface).called(1);
    verify(preferencesBoundaryMock.initStorage).called(1);
    // Make sure the UI was notified about the missing route DB
    verify(() => presentationBoundaryMock.updateRouteDbStatus(null)).called(1);
    // Make sure the UI started in the settings domain
    verify(presentationBoundaryMock.showSettings).called(1);
  });
}
