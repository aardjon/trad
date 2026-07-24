///
/// Definition of the [Sector] entity class.
///
library;

/// A single sector.
///
/// A sector is a geographical area with several summits. It is usually a part of a larger climbing
/// area. The
class Sector {
  /// Internal ID which globally identifies this sector. Not meant to be shown to users.
  int id;

  /// The name of the sector.
  String name;

  /// Constructor for directly initializing all members.
  Sector(this.id, this.name);
}
