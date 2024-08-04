///
/// Definition of the [Route] entity class.
///
library;

/// A single climbing route.
///
/// A route is the path by which a climber reaches the top of a mountain, so it is always attached
/// to a single summit. In most cases, there are multiple routes onto each summit.
class Route {
  /// Internal ID which globally identifies this climbing route. Not meant to be shown to users.
  int id;

  /// The name of the route.
  String routeName;

  /// The (technical) grade (difficulty) of the route.
  String routeGrade;

  /// A community rating of the route.
  double? routeRating;

  /// Constructor for directly initializing all members.
  Route(this.id, this.routeName, this.routeGrade, this.routeRating);
}
