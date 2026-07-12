///
/// Unit tests for the trad.core.entities.geoposition library.
///
library;

import 'dart:math';

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

  /// Test cases for bounding square calculation:
  ///
  /// - The center point is really inside the returned square
  /// - "North" latitude is larger than the "south" one
  /// - "West" longitude is lower than the "east" one
  /// - Works for smaller as well as for larger distances
  /// - The distance between the returned points and the center is correct
  /// - The shortest distance between the center and all edges equals the radius
  ///
  /// We trust on calculateDistance() returning the correct result, because this method is already
  /// tested separately.
  group('Bounding square calculation', () {
    List<(GeoPosition, int)> testData = <(GeoPosition, int)>[
      // Check "extreme" coords, i.e. largest and lowest values within the Saxon Switzerland area
      (GeoPosition(50.9950007, 13.9559331), 500), // Northernmost summit (Buch)
      (GeoPosition(50.8101536, 14.0609472), 500), // Southernmost summit (Xerxes)
      (GeoPosition(50.8996831, 14.3825167), 500), // Easternmost summit (Gamskopf)
      (GeoPosition(50.8655481, 13.9320509), 500), // Westernmost summit (Brandstein)
      // Check for different radius values
      (GeoPosition(50.9424815, 14.0396597), 999),
      (GeoPosition(50.9424815, 14.0396597), 666),
      (GeoPosition(50.9424815, 14.0396597), 333),
      (GeoPosition(50.9424815, 14.0396597), 111),
      (GeoPosition(50.9424815, 14.0396597), 22),
      (GeoPosition(50.9424815, 14.0396597), 5),
    ];
    // Because the calculations include floating point operations, we allow small inaccuracies of 10
    // centimeters when comparing.
    const double accuracy = 0.1;

    for (final (GeoPosition, int) params in testData) {
      GeoPosition center = params.$1;
      int radius = params.$2;
      test('$radius m: $center', () {
        (GeoPosition, GeoPosition) corners = center.calculateBoundingSquare(radius);
        GeoPosition northWest = corners.$1;
        GeoPosition southEast = corners.$2;

        // Ensure the order of the latitudinal and longitudinal values (i.e. the returned points are
        // really north-west and south-east). This also makes sure the center is really inside the
        // square.
        expect(northWest.latitude > center.latitude, isTrue);
        expect(center.latitude > southEast.latitude, isTrue);
        expect(northWest.longitude < center.longitude, isTrue);
        expect(center.longitude < southEast.longitude, isTrue);

        // Distance between the center and the middle of all edges is the radius.
        GeoPosition westernEdgeCenter = GeoPosition(center.latitude, northWest.longitude);
        GeoPosition easternEdgeCenter = GeoPosition(center.latitude, southEast.longitude);
        GeoPosition northernEdgeCenter = GeoPosition(northWest.latitude, center.longitude);
        GeoPosition southernEdgeCenter = GeoPosition(southEast.latitude, center.longitude);
        expect(northernEdgeCenter.calculateDistance(center), closeTo(radius, accuracy));
        expect(southernEdgeCenter.calculateDistance(center), closeTo(radius, accuracy));
        expect(easternEdgeCenter.calculateDistance(center), closeTo(radius, accuracy));
        expect(westernEdgeCenter.calculateDistance(center), closeTo(radius, accuracy));

        // Distance between the center and the corners must be correct (according to the Pythagorean
        // theorem).
        double expectedCornerDistance = sqrt(2 * (radius * radius));
        double nwDistance = northWest.calculateDistance(center);
        double seDistance = southEast.calculateDistance(center);

        expect(nwDistance, closeTo(expectedCornerDistance, accuracy));
        expect(seDistance, closeTo(expectedCornerDistance, accuracy));
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
