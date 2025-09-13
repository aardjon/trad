///
/// Definition of the boundary between the system environment adapter and external apps (via the
/// concrete operating system), between the `adapters` and the `infrastructure` rings.
///
library;

/// Abstract interface providing operations for interacting with external applications installed on
/// the same device.
abstract interface class ExternalAppsBoundary {
  /// Open an external app which is appropriate for displaying geo position URIs, and send the given
  /// [geoUri] to it. [geoUri] must be a URI with the 'geo' scheme (otherwise, a FormatException is
  /// thrown). The actual app to open is chosen by the operating system, and the actual handling of
  /// the URI is up to this app.
  Future<void> openGeoUri(Uri geoUri);
}
