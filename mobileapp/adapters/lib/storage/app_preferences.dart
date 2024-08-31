///
/// Definition of the application preferences storage adapter.
///
library;

import 'package:core/boundaries/storage/preferences.dart';
import 'package:core/entities/sorting/posts_filter_mode.dart';
import 'package:core/entities/sorting/routes_filter_mode.dart';
import 'package:crosscuttings/di.dart';

import '../boundaries/repositories/key_value_store.dart';
import '../src/storage/app_config.dart';

/// Implementation of the storage adapter used by the core to store application preferences.
///
/// This class is the place where all the concrete config keys and values are known. It also defines
/// the initial/default value if a requested setting is not yet available.
class PreferencesStorage implements AppPreferencesBoundary {
  /// The key-value store repository.
  final KeyValueStoreBoundary _repository;

  /// Constructor for using the given [dependencyProvider] to obtain dependencies from other rings.
  PreferencesStorage(DependencyProvider dependencyProvider)
      : _repository = dependencyProvider.provide<KeyValueStoreBoundary>();

  @override
  Future<void> initStorage() async {
    await _repository.initialize();
  }

  @override
  Future<PostsFilterMode> getInitialPostsSortCriterion() async {
    PostsFilterMode? sortCriterion = await _repository.getEnum<PostsFilterMode>(
      AppConfigKeys.routedbPostsSortCriterion,
      PostsFilterMode.values,
    );
    // Return a default value if the config doesn't contain one yet
    return sortCriterion ?? AppConfigDefaultValues.routedbPostsSortCriterion;
  }

  @override
  Future<RoutesFilterMode> getInitialRoutesSortCriterion() async {
    RoutesFilterMode? sortCriterion = await _repository.getEnum<RoutesFilterMode>(
      AppConfigKeys.routedbRoutesSortCriterion,
      RoutesFilterMode.values,
    );
    // Return a default value if the config doesn't contain one yet
    return sortCriterion ?? AppConfigDefaultValues.routedbRoutesSortCriterion;
  }

  @override
  Future<void> setInitialPostsSortCriterion(PostsFilterMode sortCriterion) async {
    await _repository.setEnum(key: AppConfigKeys.routedbPostsSortCriterion, value: sortCriterion);
  }

  @override
  Future<void> setInitialRoutesSortCriterium(RoutesFilterMode sortCriterion) async {
    await _repository.setEnum(key: AppConfigKeys.routedbRoutesSortCriterion, value: sortCriterion);
  }
}
