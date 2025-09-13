///
/// Implementation of the system environment adapter component.
///
library;

import 'dart:io';

import 'package:core/boundaries/sysenv.dart';
import 'package:core/entities/geoposition.dart';
import 'package:crosscuttings/di.dart';

import 'boundaries/external_apps.dart';
import 'boundaries/paths.dart';

/// The system environment adapter component.
///
/// This component is responsible for abstracting from the concrete implementation(s) of where to
/// get system specific information from.
class SystemEnvironment implements SystemEnvironmentBoundary {
  /// Interface to the system environment component, used to retrieve environment specific
  /// information.
  final PathProviderBoundary _pathProviderBoundary;

  /// Interface for interacting with other, external applications on the same device.
  final ExternalAppsBoundary _externalAppsBoundary;

  /// Constructor for using the dependency provider given as [di] to obtain dependencies from other
  /// rings.
  SystemEnvironment(DependencyProvider di)
    : _pathProviderBoundary = di.provide<PathProviderBoundary>(),
      _externalAppsBoundary = di.provide<ExternalAppsBoundary>();

  @override
  Future<String> getAppDataPath() async {
    Directory appDataDir = await _pathProviderBoundary.getAppDataDir();
    return appDataDir.path;
  }

  @override
  Future<void> openExternalMapsApp(GeoPosition markPosition) async {
    Uri geoUri = Uri(scheme: 'geo', path: '${markPosition.latitude},${markPosition.longitude}');
    await _externalAppsBoundary.openGeoUri(geoUri);
  }
}
