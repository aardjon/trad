///
/// Definition of the boundary between the system environment adapter and a concrete system
/// implementation (`adapters` ring and `infrastructure` ring).
///
library;

import 'dart:io';

/// Abstract interface providing system specific file system paths for certain usages.
abstract interface class PathProviderBoundary {
  /// Returns the full path to the application data directory.
  Future<Directory> getAppDataDir();
}
