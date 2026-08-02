///
/// Definiton of the boundary between the core and the positiong component.
///
library;

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

/// Generic base type for all exception thrown when an operation fails due to missing permissions.
class PermissionError implements Exception {
  /// The connection string of the storage that failed to start.
  final String connectionString;

  /// Constructor for directly initializing all members.
  PermissionError(this.connectionString);

  @override
  String toString() {
    return 'PermissionError: $connectionString';
  }
}

/// Thrown when a permission is not granted but may if we ask for it.
/// This can happen e.g. when this permission is needed for the very first time, and the user did
/// not yet decide whether to grant it or not. So if this exception is thrown, it's usually a good
/// idea display a short explanation to the user, ask for granting the permission and try again.
class MissingPermission extends PermissionError {
  /// Constructor for directly initializing all members.
  MissingPermission(super.connectionString);

  @override
  String toString() {
    return 'MissingPermission: ';
  }
}

/// Thrown when a permission is denied by the user or the operating system.
/// Unlike MissingPermission, the permission has been explicitly denied, so don't ask the user to
/// grant it over and over again. It might be a good idea so display a short explanation of why
/// something is not possible, though.
class PermissionDenied extends PermissionError {
  /// Constructor for directly initializing all members.
  PermissionDenied(super.connectionString);

  @override
  String toString() {
    return 'PermissionDenied: ';
  }
}

/// Thrown when a requested resource (e.g. a device or a service) is not available.
/// This usually means that e.g. a necessary device has been disabled or disconnected, so the user
/// may want to know about it.
class ResourceUnavailable implements Exception {
  @override
  String toString() {
    return 'ResourceUnavailable';
  }
}
