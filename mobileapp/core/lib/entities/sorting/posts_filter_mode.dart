///
/// Provides types to represent sort criteria for post lists.
///
library;

/// The criteria by which the post list can be sorted.
enum PostsFilterMode {
  /// Sort by date, descending.
  newestFirst,

  /// Sort by date, ascending.
  oldestFirst,
}
