///
/// Collection of errors that can be thrown from all rings.
///
library;

/// Generic base type for all exception thrown when an operation fails due to missing permissions.
class PermissionError implements Exception {
  /// Identifying name of the permission that caused problems, e.g. the missing one. This name is
  /// mainly meant for debugging.
  final String permissionName;

  /// Constructor for directly initializing all members.
  PermissionError(this.permissionName);

  @override
  String toString() {
    return 'PermissionError: $permissionName';
  }
}

/// Thrown when a permission is not granted but may if we ask for it.
/// This can happen e.g. when this permission is needed for the very first time, and the user did
/// not yet decide whether to grant it or not. So if this exception is thrown, it's usually a good
/// idea display a short explanation to the user, ask for granting the permission and try again.
class MissingPermission extends PermissionError {
  /// Constructor for directly initializing all members.
  MissingPermission(super.permissionName);

  @override
  String toString() {
    return 'MissingPermission: $permissionName';
  }
}

/// Thrown when a permission is denied by the user or the operating system.
/// Unlike MissingPermission, the permission has been explicitly denied, so don't ask the user to
/// grant it over and over again. It might be a good idea so display a short explanation of why
/// something is not possible, though.
class PermissionDenied extends PermissionError {
  /// Constructor for directly initializing all members.
  PermissionDenied(super.permissionName);

  @override
  String toString() {
    return 'PermissionDenied: $permissionName';
  }
}

/// Thrown when a requested resource (e.g. a device or a service) is not available.
/// This usually means that e.g. a necessary device has been disabled or disconnected, so the user
/// may want to know about it.
class ResourceUnavailable implements Exception {
  /// An identifiying name of the unavailable resource. This name is only meant for debugging.
  final String resourceName;

  /// Constructor for directly initializing all members.
  ResourceUnavailable(this.resourceName);

  @override
  String toString() {
    return 'ResourceUnavailable $resourceName';
  }
}
