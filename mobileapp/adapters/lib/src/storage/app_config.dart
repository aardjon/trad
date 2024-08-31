///
/// Contains static information about the application config, e.g. allowed config keys and default
/// values.
///
library;

import 'package:core/entities/sorting/posts_filter_mode.dart';
import 'package:core/entities/sorting/routes_filter_mode.dart';

/// Represents the keys that are used in the application config.
///
/// The main purpose of this class is to provide a namespace with all string constants corresponding
/// to configuration keys. Always use these constants when referring to config values to make future
/// changes easier.
class AppConfigKeys {
  /// The criterion by which the posts list shall be sorted initially.
  static const String routedbPostsSortCriterion = 'routedb.postsSortCriterion';

  /// The criterion by which the routes list shall be sorted initially.
  static const String routedbRoutesSortCriterion = 'routedb.routesSortCriterion';
}

/// Represents the default config values that shall be used in the application config cannot provide
/// one for a certain key.
///
/// The main purpose of this class is to provide a namespace with all default values for all config
/// keys. Always use these constants when referring to default config values to keep a single source
/// of truth and to make future changes easier.
class AppConfigDefaultValues {
  /// The criterion by which the posts list shall be sorted by default.
  static const PostsFilterMode routedbPostsSortCriterion = PostsFilterMode.newestFirst;

  /// The criterion by which the routes list shall be sorted by default.
  static const RoutesFilterMode routedbRoutesSortCriterion = RoutesFilterMode.name;
}
