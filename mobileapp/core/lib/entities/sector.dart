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
  final int id;

  /// The name of the sector.
  final String name;

  /// Constructor for directly initializing all members.
  const Sector(this.id, this.name);
}
