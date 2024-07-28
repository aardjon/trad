///
/// Definition of the [Summit] entity class.
///
library;

/// A single summit.
///
/// A summit is a single rock or mountain that can be climbed onto. There are usually several routes
/// to the top.
class Summit {
  /// Internal ID which globally identifies this summit. Not meant to be shown to users.
  int id;

  /// The name of the summit.
  String name;

  /// Constructor for directly initializing all members.
  Summit(this.id, this.name);
}
