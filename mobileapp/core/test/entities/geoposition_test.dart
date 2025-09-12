///
/// Unit tests for the trad.core.entities.geoposition library.
///
library;

import 'package:core/entities/geoposition.dart';
import 'package:test/test.dart';

void main() {
  /// Test cases for trying to create GeoPositions with invalid coordinate values
  /// Should cause an assertion
  group('Invalid GeoPositions', () {
    List<(double, double)> invalidCoordinates = <(double, double)>[
      (91.0, 13.456),
      (51.876, 181.0),
      (-91.0, -13.456),
      (-51.876, -181.0),
      (91.0, 181.0),
    ];
    for (final (double, double) coords in invalidCoordinates) {
      test('$coords', () {
        expect(() {
          GeoPosition(coords.$1, coords.$2);
        }, throwsA(isA<AssertionError>()));
      });
    }
  });

  /// Test cases for creating valid GeoPositions, including some corner/extreme values
  group('Successful GeoPosition creation', () {
    List<(double, double)> testData = <(double, double)>[
      (0.0, 0.0),
      (51.765, 13.456),
      (-51.765, -13.456),
      (90.0, 13.456),
      (-90.0, 13.456),
      (51.765, 180.0),
      (51.765, -180.0),
      (90.0, 180.0),
      (-90.0, -180.0),
    ];
    for (final (double, double) coords in testData) {
      double lat = coords.$1;
      double lon = coords.$2;

      test('$coords', () {
        GeoPosition geoPos = GeoPosition(lat, lon);
        expect(geoPos.latitude, equals(lat));
        expect(geoPos.longitude, equals(lon));
      });
    }
  });
}
