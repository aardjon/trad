///
/// Dumb adapter to connect the core PositioningBound
///
library;

import 'package:core/boundaries/positioning.dart';
import 'package:core/entities/geoposition.dart';

import 'boundaries/positioning.dart';

/// Dumb adapter that connects the core PositioningBoundary with the actual implemention.
class LocationAdapter implements PositioningBoundary {
  final LocationBoundary _locationImpl;

  /// Constructor for directly initialzing all members.
  LocationAdapter(this._locationImpl);

  @override
  Future<void> requestPermissions() {
    return _locationImpl.requestPermissions();
  }

  @override
  Future<GeoPosition> getCurrentPosition() async {
    (double, double) geoData = await _locationImpl.getCurrentPosition();
    return GeoPosition(geoData.$1, geoData.$2);
  }
}
