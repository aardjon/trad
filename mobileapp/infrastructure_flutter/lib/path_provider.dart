///
/// Flutter implementation of a component providing system paths.
///
library;

import 'dart:io';

import 'package:path_provider/path_provider.dart';

import 'package:adapters/boundaries/paths.dart';

/// Flutter & path_provider based implementation of the [PathProviderBoundary].
///
/// This implementation uses the `path_provider` Flutter plugin package to determine concrete,
/// system specific paths. It's main purpose is to completely hide all details and the API of this
/// plugin, so that only this component needs to be changed at all when there are incompatible
/// upstream changes.
class SystemPathProvider implements PathProviderBoundary {
  @override
  Future<Directory> getAppDataDir() async {
    Directory dataDir = await getApplicationSupportDirectory();
    return Directory(dataDir.absolute.path);
  }
}
