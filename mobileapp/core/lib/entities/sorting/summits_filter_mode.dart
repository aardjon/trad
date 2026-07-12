///
/// Provides types to represent sort criteria for summit lists.
///
library;

/// The criteria by which the list of nearby summits can be sorted.
enum NearbySummitsSortMode {
  /// Sort alphabetically by summit names.
  name,

  /// Sort by distance.
  distance,
}
