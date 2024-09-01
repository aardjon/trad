///
/// Definition of the boundary between the core and the application preferences storage.
///
library;

import '../../entities/sorting/posts_filter_mode.dart';
import '../../entities/sorting/routes_filter_mode.dart';

/// Interface providing application preferences data to the core.
///
/// Application preferences data is a set of rather small data that needs to be persisted between
/// application runs but is not actual user data (which may be explicitly written loaded or
/// exchanged by the user). It's typically used for storing some internal state to be recovered for
/// the next run, for storing user preferences about the application itself. Preferences data is not
/// meant to be shared with other application, and may be deleted or reset at any time.
abstract interface class AppPreferencesBoundary {
  /// Initializes the storage.
  ///
  /// An exception is thrown if the storage cannot be initialized for some reason.
  Future<void> initStorage();

  /// Returns the sort criterion that shall be used to initially order the posts within the post
  /// list.
  Future<PostsFilterMode> getInitialPostsSortCriterion();

  /// Stores the [sortCriterion] that shall be used to initially order the posts within the post
  /// list.
  Future<void> setInitialPostsSortCriterion(PostsFilterMode sortCriterion);

  /// Returns the sort criterion that shall be used to initially order the routes within the route
  /// list.
  Future<RoutesFilterMode> getInitialRoutesSortCriterion();

  /// Stores the [sortCriterion] that shall be used to initially order the routes within the route
  /// list.
  Future<void> setInitialRoutesSortCriterion(RoutesFilterMode sortCriterion);
}
