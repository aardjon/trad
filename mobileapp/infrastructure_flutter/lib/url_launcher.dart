///
/// Flutter implementation of a component for opening URLs by launching external apps.
///
library;

import 'package:adapters/boundaries/external_apps.dart';
import 'package:url_launcher/url_launcher.dart';

/// Concrete ExternalAppsBoundary implementation based on the url_launcher Flutter plugin.
/// Plugin API documentation: https://pub.dev/documentation/url_launcher/latest/
class UrlLauncher implements ExternalAppsBoundary {
  @override
  Future<void> openGeoUri(Uri geoUri) async {
    if (!geoUri.isScheme('geo')) {
      throw FormatException('Cannot launch maps app for Non-Geo-URI $geoUri');
    }

    // Workaround for everyone using Google Maps: Also add the coordinates as query parameter,
    // otherwise GM won't display a map PIN. See also https://en.wikipedia.org/wiki/Geo_URI_scheme
    Uri extendedUri = geoUri.replace(queryParameters: <String, dynamic>{'q': geoUri.path});

    await launchUrl(extendedUri);
  }
}
