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

  /// Test cases for distance calculation:
  ///
  /// - Calculation must return the expected distance value
  /// - Both operands can be the same
  /// - Operand order doesn't matter
  ///
  /// Because the distance calculation is a floating point operation, we allow small inaccuracies
  /// when comparing.
  group('Distance calculation', () {
    /* Test data:
     GeoPosition(50.9424815, 14.0396597) --> "Rhombus"
     GeoPosition(50.9421666, 14.0399232) --> "Bärensteinscheibe"
     The distance between them is about 39.6 meters.
     */
    List<(GeoPosition, GeoPosition, double)> testData = <(GeoPosition, GeoPosition, double)>[
      (GeoPosition(50.9424815, 14.0396597), GeoPosition(50.9421666, 14.0399232), 39.6),
      (GeoPosition(50.9421666, 14.0399232), GeoPosition(50.9424815, 14.0396597), 39.6),
      (GeoPosition(50.9421666, 14.0399232), GeoPosition(50.9421666, 14.0399232), 0.0),
    ];
    const double accuracy = 0.1; // We accept a difference of 10 centimeters
    for (final (GeoPosition, GeoPosition, double) params in testData) {
      GeoPosition pos1 = params.$1;
      GeoPosition pos2 = params.$2;
      double expectedDistance = params.$3;
      test('$pos1 - $pos2', () {
        double distance = pos1.calculateDistance(pos2);
        expect(distance, closeTo(expectedDistance, accuracy));
      });
    }
  });

  /// Test cases for GeoPosition string conversion
  group('String conversion', () {
    List<(double, double, String)> testData = <(double, double, String)>[
      (51.765, 13.456, '51.7650000°N 13.4560000°E'),
      (-51.765, -13.456, '51.7650000°S 13.4560000°W'),
      (51.765, -13.456, '51.7650000°N 13.4560000°W'),
      (-51.765, 13.456, '51.7650000°S 13.4560000°E'),
    ];
    for (final (double, double, String) coords in testData) {
      double lat = coords.$1;
      double lon = coords.$2;
      String expected = coords.$3;
      test(expected, () {
        expect(GeoPosition(lat, lon).toString(), expected);
      });
    }
  });
}
