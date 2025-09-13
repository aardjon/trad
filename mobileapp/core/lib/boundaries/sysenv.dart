///
/// Definition of the boundary between the core and the system environment adapter.
///
library;

import '../entities/geoposition.dart';

/// Interface representing the concrete operating system environment we're currently running on.
///
/// Provides system information as well as methods to trigger OS actions.
abstract interface class SystemEnvironmentBoundary {
  /// Returns the URI to the application data directory.
  ///
  /// This directory is the place for storing persistent, application specific data, so write
  /// permission can usually be assumed. However, whether other applications can also read it
  /// depends on the operating system, so sensitive data must still be secured properly.
  Future<String> getAppDataPath();

  /// Requests the operating system to open an external map application to display the given
  /// [markPosition] there. Which application is used (or how to choose between multiple options) is
  /// up to the system.
  // TODO(aardjon): This request may fail, or the user may cancel it. Do we want to know this?
  Future<void> openExternalMapsApp(GeoPosition markPosition);
}
