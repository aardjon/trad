///
/// Implementation of the system environment adapter component.
///
library;

import 'dart:io';

import 'package:core/boundaries/sysenv.dart';
import 'package:crosscuttings/di.dart';

import 'boundaries/paths.dart';

/// The system environment adapter component.
///
/// This component is responsible for abstracting from the concrete implementation(s) of where to
/// get system specific information from.
class SystemEnvironment implements SystemEnvironmentBoundary {
  /// Interface to the system environment component, used to retrieve environment specific
  /// information.
  final PathProviderBoundary _pathProviderBoundary;

  /// Constructor for using the dependency provider given as [di] to obtain dependencies from other
  /// rings.
  SystemEnvironment(DependencyProvider di)
      : _pathProviderBoundary = di.provide<PathProviderBoundary>();

  @override
  Future<String> getAppDataPath() async {
    Directory appDataDir = await _pathProviderBoundary.getAppDataDir();
    return appDataDir.path;
  }
}
