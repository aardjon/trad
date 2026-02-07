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
  Difficulty grade;

  /// True if the route is officially marked as "dangerous", false if not.
  bool dangerous;

  /// The count of stars assigned to this route in the official rating. An increasing number of
  /// stars marks a route as "more beautiful". 0 is the default for regular routes.
  int stars;

  /// A community rating of the route.
  double? routeRating;

  /// Constructor for directly initializing all members.
  Route({
    required this.id,
    required this.routeName,
    required this.grade,
    this.dangerous = false,
    this.stars = 0,
    this.routeRating,
  });

  @override
  String toString() {
    return "${super.toString()}: '$routeName'";
  }
}

/// Describes the (technical) difficulty of a single route, aggregating different aspects.
/// The different grades are positive numbers. Even though the scales have no defined open ends,
/// we only support values up to one grade above the highest grade that currently exists in the
/// Saxon Switzerland area.
/// All fields can be set to 0, meaning that the aspect is not relevant for this route. However, at
/// least one grade must always be defined for an instance to be valid.
class Difficulty {
  /// Special value to use when a certain grade is not assigned
  static const int noGrade = 0;

  /// Difficulty of the jump within this route, if the route contains a jump.
  int jump;

  /// The grade that applies when climbing this route in the AF ("alles frei", i.e. "all free")
  /// style. This is the default style which always applied nothing nothing else is specifiedbe set
  /// as long as there is a climb at all. Set to 0 for pure jump routes.
  int af;

  /// The grade that applies when climbing this route in the OU ("ohne Unterstützung", i.e. "without
  /// support") style, i.e. without using the support considered in the AF style grade.
  int ou;

  /// The grade that applies when climbing this route in the RP ("Rotpunkt", i.e. "redpoint") style.
  int rp;

  /// Constructor for directly initializing all members.
  Difficulty({this.af = noGrade, this.ou = noGrade, this.rp = noGrade, this.jump = noGrade})
    : assert(
        !(af == noGrade && ou == noGrade && rp == noGrade && jump == noGrade),
        'At least one grade must be set',
      ),
      assert(
        (af >= noGrade && ou >= noGrade && rp >= noGrade && jump >= noGrade),
        'Grade values must not be negative',
      );

  @override
  String toString() {
    List<String> parts = <String>[];
    if (jump != noGrade) {
      parts.add('j=$jump');
    }
    if (af != noGrade) {
      parts.add('af=$af');
    }
    if (ou != noGrade) {
      parts.add('ou=$ou');
    }
    if (rp != noGrade) {
      parts.add('rp=$rp');
    }
    return 'Difficulty(${parts.join(",")})';
  }
}
