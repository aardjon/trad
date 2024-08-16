///
/// Definition of the boundary between the core and the system environment adapter.
///
library;

/// Interface providing information about the concrete system environment we're currently running
/// on.
abstract interface class SystemEnvironmentBoundary {
  /// Returns the URI to the application data directory.
  ///
  /// This directory is the place for storing persistent, application specific data, so write
  /// permission can usually be assumed. However, whether other applications can also read it
  /// depends on the operating system, so sensitive data must still be secured properly.
  Future<Uri> getAppDataPath();
}
