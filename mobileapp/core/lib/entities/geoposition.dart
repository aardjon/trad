///
/// Definition of the [GeoPosition] entity class.
///
library;

/// A single geographical point in the WGS 84 geodetic system.
///
/// The coordinates are represented in decimal degree, with the latitude value being within
/// [-90.0, 90.0] and the longitude value being within [-180.0, 180.0]. Positive values are
/// North/East, negative values are South/West.
///
/// The maximum precision of geographic coordinates is about 1 cm (7 decimal places), which is the
/// same as used by OSM. Please note that due to the floating point representation, values and
/// calculations may be less accurate.
///
/// GeoPosition does not override the equality operator (==) on purpose, because the meaning of
/// "equal positions" is not exactly intuitive and can depend on the use cases.
class GeoPosition {
  /// The latitude value in decimal degree.
  final double latitude;

  /// The longitude value in decimal degree.
  final double longitude;

  /// Constructor for directly initializing all members.
  ///
  /// Raises if the given values exceed the allowed value range.
  GeoPosition(this.latitude, this.longitude)
    : assert(latitude >= -90.0 && latitude <= 90.0, 'Latitude value must be within [-90.0, 90.0]'),
      assert(
        longitude >= -180.0 && longitude <= 180.0,
        'Longitude value must be within [-180.0, 180.0]',
      );

  @override
  String toString() {
    String hemisphereLat = latitude >= 0.0 ? 'N' : 'S';
    String hemisphereLon = longitude >= 0.0 ? 'E' : 'W';
    String latStr = latitude.toStringAsFixed(7);
    String lonStr = longitude.toStringAsFixed(7);
    return '$latStr°$hemisphereLat $lonStr°$hemisphereLon';
  }
}
