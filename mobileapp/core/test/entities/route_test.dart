///
/// Unit tests for the trad.core.entities.route library.
///
library;

import 'package:core/entities/route.dart';
import 'package:test/test.dart';

void main() {
  /// Unit tests for the Difficulty class.
  group('Difficulty() tests', () {
    /// Ensure the correct behaviour in case all constructor parameters are 0.
    test('all-zero', () {
      expect(() {
        Difficulty(af: 0, rp: 0, ou: 0, jump: 0);
      }, throwsA(isA<AssertionError>()));
    });

    /// Ensure the correct behaviour for a negative constructor parameter.
    List<(String, void Function())> testParams = <(String, void Function())>[
      ('jump', () => Difficulty(jump: -1)),
      (
        'af',
        () {
          Difficulty(af: -1);
        },
      ),
      (
        'ou',
        () {
          Difficulty(ou: -1);
        },
      ),
      (
        'rp',
        () {
          Difficulty(rp: -1);
        },
      ),
    ];
    for (final (String, void Function()) params in testParams) {
      final String label = params.$1;
      final void Function() creator = params.$2;
      test('negative value: $label}', () {
        expect(creator, throwsA(isA<AssertionError>()));
      });
    }
  });
}
