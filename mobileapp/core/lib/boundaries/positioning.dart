///
/// Definiton of the boundary between the core and the positiong component.
///
library;

import 'package:crosscuttings/errors.dart';
import '../entities/geoposition.dart';

/// Interface providing the current location (as in geographical position).
abstract interface class PositioningBoundary {
  /// Request all required permissions to get a position from the operating system. This may be
  /// successful when another method raised [MissingPermission], but should be avoided after a
  /// [PermissionDenied] to not bother the user unnecessarily.
  ///
  /// Throws [ResourceUnavailable] if the Location service is not available at all (maybe the
  /// user disabled it or the platform doesn't provide the necessary GPS device).
  Future<void> requestPermissions();

  /// Return the current geographical position, as reported by the operating system.
  ///
  /// Throws an exception in case of errors:
  ///  - PermissionError: The application is not allowed to access the location, either because the
  ///    user explicitly denied the permission ([PermissionDenied]) or didn't decide yet
  ///    ([MissingPermission]).
  ///  - ResourceUnavailable: The Location service is not available, maybe the user disabled it or
  ///    the platform doesn't provide the necessary GPS device at all.
  ///
  /// Note that retrieving the position may take a while.
  Future<GeoPosition> getCurrentPosition();
}
