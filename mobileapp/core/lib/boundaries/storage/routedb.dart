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
///
/// This storage can be in one of two possible states (STOPPED and STARTED) which can be changed by
/// [startStorage] and [stopStorage]. Most methods require a certain state to work, otherwise they
/// usually throw a StateError. For example, all of the `retrieve*()` methods can only be called
/// when the storage is STARTED.
abstract interface class RouteDbStorageBoundary {
  /// Starts the storage, changing its state to STARTED.
  ///
  /// An exception is thrown if the storage cannot be started (e.g. because of the database file
  /// being not found or invalid).
  Future<void> startStorage();

  /// Stops the storage, changing its state to STOPPED.
  ///
  /// This is the opposite operation of [startStorage], it closes all connections to the storage and
  /// releases all resources. If the storage is already STOPPED, this method does nothing.
  void stopStorage();

  /// Returns true if the storage is in the STARTED state (i.e. [startStorage] has been called), or
  /// false otherwise.
  bool isStarted();

  /// Imports the database file at the given [filePath] as new route database, completely replacing
  /// the previous route database (if any).
  ///
  /// This must only be called on a STOPPED storage.
  ///
  /// Possible exceptions:
  ///  - StateError: The storage has not been stopped before
  ///  - PathNotFoundException: The provided [filePath] doesn't exist or is not a file
  Future<void> importRouteDbFile(String filePath);

  /// Retrieve all data of the single summit identified by [summitDataId].
  ///
  /// This must only be called on a STARTED storage.
  Future<Summit> retrieveSummit(int summitDataId);

  /// Retrieve all data of the single route identified by [routeDataId].
  ///
  /// This must only be called on a STARTED storage.
  Future<Route> retrieveRoute(int routeDataId);

  /// Retrieve all summit data matching the given [nameFilter] from the storage.
  ///
  /// If a filter string is given, only the summits whose name contains it are returned. If no
  /// filter is given, all summits are returned.
  ///
  /// This must only be called on a STARTED storage.
  Future<List<Summit>> retrieveSummits([String? nameFilter]);

  /// Retrieve all [Route]s to the requested summit (identified by [summitId]).
  ///
  /// The returned items are ordered by the given [sortCriterion]. If the given [summitId] is not a
  /// valid/existing summit ID, an empty list is returned.
  ///
  /// This must only be called on a STARTED storage.
  Future<List<Route>> retrieveRoutesOfSummit(int summitId, RoutesFilterMode sortCriterion);

  /// Retrieve all [Post]s for the requested route (identified by [routeId]).
  ///
  /// The returned items are ordered by the given [sortCriterion]. If the given [routeId] is not a
  /// valid/existing route ID, an empty list is returned.
  ///
  /// This must only be called on a STARTED storage.
  Future<List<Post>> retrievePostsOfRoute(int routeId, PostsFilterMode sortCriterion);
}
