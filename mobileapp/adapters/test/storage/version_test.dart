///
/// Unit tests for the adapters.storage.version library.
///
library;

import 'package:test/test.dart';

import 'package:adapters/src/storage/version.dart';

/// Unit tests for the adapters.storage.version.Version class.
void main() {
  /// Test cases for the class constructor
  group('construction', () {
    /// Checks the construction with some valid values.
    List<(int, int)> validVersionConstructions = <(int, int)>[
      (1, 0),
      (1, 999),
      (1000, 1),
      (0, 0),
    ];

    for (final (int, int) versionParams in validVersionConstructions) {
      test('valid values: ${versionParams.$1}, ${versionParams.$2}', () {
        Version version = Version(versionParams.$1, versionParams.$2);
        expect(version.major == versionParams.$1, isTrue);
        expect(version.minor == versionParams.$2, isTrue);
      });
    }

    /// Ensures that invalid values are rejected:
    ///  - Negative value for one or both parameters
    ///  - Minor part of 1000 or higher
    List<(int, int)> invalidValues = <(int, int)>[
      (-1, 0),
      (1, -1),
      (1, 1000),
    ];

    for (final (int, int) versionParams in invalidValues) {
      test('invalid values: ${versionParams.$1}, ${versionParams.$2}', () {
        expect(
          () => Version(versionParams.$1, versionParams.$2),
          throwsArgumentError,
        );
      });
    }
  });

  /// Test cases for the comparison operators
  group('comparison operators', () {
    /// Ensures the correct behaviour of all comparison operators.
    List<(bool Function(), Matcher)> operatorTestParams = <(bool Function(), Matcher)>[
      // Equality
      (() => Version(1, 2) == Version(1, 2), isTrue),
      (() => Version(1, 2) == Version(2, 1), isFalse),
      (() => Version(1, 2) == Version(1, 1), isFalse),
      // Lower than
      (() => Version(1, 2) < Version(1, 1), isFalse),
      (() => Version(1, 1) < Version(1, 2), isTrue),
      (() => Version(1, 2) < Version(2, 1), isTrue),
      (() => Version(2, 1) < Version(1, 2), isFalse),
      (() => Version(3, 0) < Version(3, 0), isFalse),
      // Greater than
      (() => Version(1, 2) > Version(1, 1), isTrue),
      (() => Version(1, 1) > Version(1, 2), isFalse),
      (() => Version(1, 2) > Version(2, 1), isFalse),
      (() => Version(2, 1) > Version(1, 2), isTrue),
      (() => Version(3, 0) > Version(3, 0), isFalse),
      // Lower than or equal
      (() => Version(1, 2) <= Version(1, 1), isFalse),
      (() => Version(1, 1) <= Version(1, 2), isTrue),
      (() => Version(1, 2) <= Version(2, 1), isTrue),
      (() => Version(2, 1) <= Version(1, 2), isFalse),
      (() => Version(3, 0) <= Version(3, 0), isTrue),
      // Greater than or equal
      (() => Version(1, 2) >= Version(1, 1), isTrue),
      (() => Version(1, 1) >= Version(1, 2), isFalse),
      (() => Version(1, 2) >= Version(2, 1), isFalse),
      (() => Version(2, 1) >= Version(1, 2), isTrue),
      (() => Version(3, 0) >= Version(3, 0), isTrue),
    ];
    for (int i = 0; i < operatorTestParams.length; i++) {
      final (bool Function(), Matcher) testParams = operatorTestParams[i];
      test('test case $i', () {
        expect(testParams.$1(), testParams.$2);
      });
    }
  });

  /// Test cases for the isCompatible method.
  group('isCompatible', () {
    /// Ensures the correct behaviour of the isCompatible() method. A.isCompatible(B) means that
    /// version B is compatible with version A if both:
    ///  - They are of the same major version
    ///  - The minor version of B is equal or older than the one of A
    List<(Version, Version, Matcher)> compatibilityTestParams = <(Version, Version, Matcher)>[
      // Same version
      (Version(1, 2), Version(1, 2), isTrue),
      // Newer minor version
      (Version(1, 2), Version(1, 3), isFalse),
      // Older minor version
      (Version(1, 2), Version(1, 1), isTrue),
      // Different major version
      (Version(1, 2), Version(2, 2), isFalse),
      (Version(2, 2), Version(1, 2), isFalse),
    ];
    for (final (Version, Version, Matcher) testParams in compatibilityTestParams) {
      Version versionA = testParams.$1;
      Version versionB = testParams.$2;
      Matcher matcher = testParams.$3;
      test('${versionA.major}.${versionA.minor} & ${versionB.major}.${versionB.minor}', () {
        expect(versionA.isCompatible(versionB), matcher);
      });
    }
  });

  /// Test cases for the toString method, ensuring the string serialization of Versions.
  group('toString', () {
    List<(Version, String)> stringTestParams = <(Version, String)>[
      (Version(1, 2), '1.2'),
      (Version(2, 1), '2.1'),
      (Version(0, 0), '0.0'),
      (Version(999, 999), '999.999'),
    ];
    for (final (Version, String) testParams in stringTestParams) {
      Version version = testParams.$1;
      String expectedString = testParams.$2;
      test(expectedString, () {
        expect(version.toString().contains(expectedString), isTrue);
      });
    }
  });

  /// Test cases for checking the hash calculation (hashCode pproperty)
  group('hashCode', () {
    List<(Version, int)> hashTestParams = <(Version, int)>[
      (Version(1, 2), 1002),
      (Version(2, 1), 2001),
      (Version(0, 0), 0),
      (Version(999, 999), 999999),
    ];
    for (final (Version, int) testParams in hashTestParams) {
      Version version = testParams.$1;
      int expectedResult = testParams.$2;

      test('$expectedResult', () {
        expect(version.hashCode == expectedResult, isTrue);
      });
    }
  });
}
