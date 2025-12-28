///
/// Definition of the boundary between the system environment adapter and a concrete system
/// implementation (`adapters` ring and `infrastructure` ring).
///
library;

import 'dart:io';

/// Abstract interface providing system specific file system paths for certain usages.
abstract interface class PathProviderBoundary {
  /// Returns the full path to the application data directory.
  ///
  /// This is a directory for persisting application specific data, it must not be modified by other
  /// applications. The operating system may (or may not) delete it when the application is
  /// uninstalled or reset, though. Depending on the underlying platform, other users and/or
  /// applications may be able to read its contents or not.
  Future<Directory> getAppDataDir();

  /// Returns the full path to the temporary directory.
  ///
  /// The contents of this directory are not persisted and may be wiped by the operating system at
  /// any time, e.g. on system reboot. The application is guaranteed to have read and write access
  /// to it. The directory may be shared with other applications or not, so beware name collisions
  /// when creating files there.
  Future<Directory> getTempDir();
}
