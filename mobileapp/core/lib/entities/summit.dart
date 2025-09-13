///
/// Definition of the [Summit] entity class.
///
library;

import 'geoposition.dart';

/// A single summit.
///
/// A summit is a single rock or mountain that can be climbed onto. There are usually several routes
/// to the top.
class Summit {
  /// Internal ID which globally identifies this summit. Not meant to be shown to users.
  int id;

  /// The name of the summit.
  String name;

  /// The geographical position of this summit, if known. May be missing in cases without a useful,
  /// single "summit" point, which is a rare corner case that will hopefully be eliminated in the
  /// future.
  // TODO(aardjon): Make it mandatory when https://github.com/Headbucket/trad/issues/12 is done.
  final GeoPosition? position;

  /// Constructor for directly initializing all members.
  Summit(this.id, this.name, [this.position]);

  @override
  String toString() {
    return "${super.toString()}: '$name'";
  }
}
