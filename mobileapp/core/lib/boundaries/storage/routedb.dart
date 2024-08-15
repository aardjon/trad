///
/// Definition of the boundary between the core and the route storage.
///
library;

import 'dart:async';

import '../../entities/post.dart';
import '../../entities/route.dart';
import '../../entities/sorting/posts_filter_mode.dart';
import '../../entities/sorting/routes_filter_mode.dart';
import '../../entities/summit.dart';

/// Interface providing climbing route data to the core.
///
/// The route database is a read only data storage.
abstract interface class RouteDbStorageBoundary {
  /// Initializes the storage with the file provided as [routeDbFile].
  ///
  /// An exception is thrown if the storage cannot be initialized (e.g. because of the file not
  /// being found or invalid).
  void initStorage(String routeDbFile);

  /// Retrieve all data of the single summit identified by [summitDataId].
  Future<Summit> retrieveSummit(int summitDataId);

  /// Retrieve all data of the single route identified by [routeDataId].
  Future<Route> retrieveRoute(int routeDataId);

  /// Retrieve all summit data matching the given [nameFilter] from the storage.
  ///
  /// If a filter string is given, only the summits whose name contains it are returned. If no
  /// filter is given, all summits are returned.
  Future<List<Summit>> retrieveSummits([String? nameFilter]);

  /// Retrieve all [Route]s to the requested summit (identified by [summitId]).
  ///
  /// The returned items are ordered by the given [sortCriterion]. If the given [summitId] is not a
  /// valid/existing summit ID, an empty list is returned.
  Future<List<Route>> retrieveRoutesOfSummit(int summitId, RoutesFilterMode sortCriterion);

  /// Retrieve all [Post]s for the requested route (identified by [routeId]).
  ///
  /// The returned items are ordered by the given [sortCriterion]. If the given [routeId] is not a
  /// valid/existing route ID, an empty list is returned.
  Future<List<Post>> retrievePostsOfRoute(int routeId, PostsFilterMode sortCriterion);
}
