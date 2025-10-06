///
/// Unit tests for the adapters.storage.app_preferences library.
///
library;

import 'package:adapters/boundaries/repositories/key_value_store.dart';
import 'package:adapters/src/storage/app_config.dart';
import 'package:adapters/storage/app_preferences.dart';
import 'package:core/entities/sorting/posts_filter_mode.dart';
import 'package:core/entities/sorting/routes_filter_mode.dart';
import 'package:crosscuttings/di.dart';
import 'package:mocktail/mocktail.dart';
import 'package:test/test.dart';

class KeyValueStoreBoundaryMock extends Mock implements KeyValueStoreBoundary {}

/// Unit tests for the adapters.storage.app_preferences.PreferencesStorage class.
void main() {
  final KeyValueStoreBoundaryMock keyValueStoreMock = KeyValueStoreBoundaryMock();
  final DependencyProvider di = DependencyProvider();

  di.registerFactory<KeyValueStoreBoundary>(() => keyValueStoreMock);

  tearDown(() {
    // Reset the mocks after each test case
    reset(keyValueStoreMock);
  });

  /// Ensure that calling initStorage() initializes the underlying key value store.
  test('initStorage()', () async {
    when(keyValueStoreMock.initialize).thenAnswer((_) async {});
    PreferencesStorage storage = PreferencesStorage(di);
    await storage.initStorage();
    verify(keyValueStoreMock.initialize).called(1);
  });

  /// Ensure the correct behaviour of all methods regarding the sorting of routes.
  group('Routes sorting criterion', () {
    /// Ensure that routes are sorted by their name, if no other criterion was defined
    test('check default value', () async {
      when(
        () => keyValueStoreMock.getEnum<RoutesFilterMode>(
          AppConfigKeys.routedbRoutesSortCriterion,
          any(),
        ),
      ).thenAnswer((_) async {
        return null; // No value stored --> Use default
      });

      PreferencesStorage storage = PreferencesStorage(di);
      RoutesFilterMode sortCriterion = await storage.getInitialRoutesSortCriterion();

      expect(sortCriterion, equals(RoutesFilterMode.name));
    });

    /// Ensure that setting and retrieving routes sorting criteria works as expected
    for (final RoutesFilterMode criterion in RoutesFilterMode.values) {
      test('persist criterion: $criterion', () async {
        // Configure the keyValueStoreMock to accept and return the current criterion value (only)
        when(
          () => keyValueStoreMock.setEnum(
            key: AppConfigKeys.routedbRoutesSortCriterion,
            value: criterion,
          ),
        ).thenAnswer((_) async {
          return true;
        });
        when(
          () => keyValueStoreMock.getEnum<RoutesFilterMode>(
            AppConfigKeys.routedbRoutesSortCriterion,
            any(),
          ),
        ).thenAnswer((_) async {
          return criterion;
        });

        // Run the actual test case
        PreferencesStorage storage = PreferencesStorage(di);
        await storage.setInitialRoutesSortCriterion(criterion);
        RoutesFilterMode sortCriterion = await storage.getInitialRoutesSortCriterion();
        expect(sortCriterion, equals(criterion));
      });
    }
  });

  /// Ensure the correct behaviour of all methods regarding the sorting of posts.
  group('Posts sorting criterion', () {
    /// Ensure that posts are sorted "newest first", if no other criterion was defined
    test('get default Value', () async {
      when(
        () => keyValueStoreMock.getEnum<PostsFilterMode>(
          AppConfigKeys.routedbPostsSortCriterion,
          any(),
        ),
      ).thenAnswer((_) async {
        return null; // No value stored --> Use default
      });

      PreferencesStorage storage = PreferencesStorage(di);
      PostsFilterMode sortCriterion = await storage.getInitialPostsSortCriterion();

      expect(sortCriterion, equals(PostsFilterMode.newestFirst));
    });

    /// Ensure that setting and retrieving posts sorting criteria works as expected
    for (final PostsFilterMode criterion in PostsFilterMode.values) {
      test('persist criterion: $criterion', () async {
        // Configure the keyValueStoreMock to accept and return the current criterion value (only)
        when(
          () => keyValueStoreMock.setEnum(
            key: AppConfigKeys.routedbPostsSortCriterion,
            value: criterion,
          ),
        ).thenAnswer((_) async {
          return true;
        });
        when(
          () => keyValueStoreMock.getEnum<PostsFilterMode>(
            AppConfigKeys.routedbPostsSortCriterion,
            any(),
          ),
        ).thenAnswer((_) async {
          return criterion;
        });

        // Run the actual test case
        PreferencesStorage storage = PreferencesStorage(di);
        await storage.setInitialPostsSortCriterion(criterion);
        PostsFilterMode sortCriterion = await storage.getInitialPostsSortCriterion();
        expect(sortCriterion, equals(criterion));
      });
    }
  });
}
