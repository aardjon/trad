///
/// Location based implementaiton of the *positioning* component.
///
/// See https://pub.dev/packages/location for package documentation.
///
library;

import 'package:adapters/boundaries/positioning.dart';
import 'package:location/location.dart';
import 'package:crosscuttings/errors.dart';

/// Implements the Positioning component based on the Flutter *location* plugin.
///
/// Prefer to reuse the same instance between clients, because there is only one location
/// device and multiple instances will just provide the same data.
class LocationComponent implements LocationBoundary {
  /// Plugin functionality entry point.
  final Location _location = Location();

  @override
  Future<void> requestPermissions() async {
    await _ensureLocationServiceEnabled();
    await _location.requestPermission();
  }

  @override
  Future<(double, double)> getCurrentPosition() async {
    await _ensureLocationServiceEnabled();

    PermissionStatus permission = await _location.hasPermission();
    if (permission == PermissionStatus.denied) {
      throw MissingPermission('LOCATION');
    }
    if (permission == PermissionStatus.deniedForever) {
      throw PermissionDenied('LOCATION');
    }

    LocationData position = await _location.getLocation();
    return (position.latitude, position.longitude);
  }

  /// Ensure that the location services are enabled at all by raising [ResourceUnavailable], if
  /// they are not.
  Future<void> _ensureLocationServiceEnabled() async {
    if (!await _location.serviceEnabled()) {
      if (!await _location.requestService()) {
        // Location services are disabled
        throw ResourceUnavailable('LOCATION SERVICE');
      }
    }
  }
}
