///
/// Location based implementaiton of the *positioning* component.
///
/// See https://pub.dev/packages/location for package documentation.
///
library;

import 'package:adapters/boundaries/positioning.dart';
import 'package:flutter/services.dart';
import 'package:location/location.dart';
import 'package:crosscuttings/errors.dart';
import 'package:crosscuttings/logging/logger.dart';

/// Logger to be used in this library file.
final Logger _logger = Logger('trad.infrastructure_flutter.geolocation');

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
      // Package example suggests that requestService() returns false if teh service is not
      // available. But at least on Android, it raises a PlatformException. Documentation doesn't
      // say anything about this case, so better handle both possibilities.
      bool success = false;
      try {
        success = await _location.requestService();
      } on PlatformException catch (error) {
        _logger.error('Location Service Request failed with: ', error);
        success = false;
      }
      if (!success) {
        // Location services are disabled
        throw ResourceUnavailable('LOCATION SERVICE');
      }
    }
  }
}
