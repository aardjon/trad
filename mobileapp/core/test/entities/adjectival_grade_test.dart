///
/// Unit tests for the adjectival grade library.
///
library;

import 'package:test/test.dart';

import 'package:core/entities/adjectival_grade.dart';

/// Unit tests for the adjectival grade enum.
void main() {
  group('adjectivalGrade', () {
    test('toString returns correct caption', () {
      Map<AdjectivalGrade, String> expected = <AdjectivalGrade, String>{
        AdjectivalGrade.e0: 'E0',
        AdjectivalGrade.e1: 'E1',
        AdjectivalGrade.e2: 'E2',
        AdjectivalGrade.e3: 'E3',
        AdjectivalGrade.e4: 'E4',
      };

      expected.forEach((AdjectivalGrade adjectivalGrade, String exectedString) {
        String actualString = adjectivalGrade.toString();
        expect(actualString, exectedString);
      });
    });

    test('greater than operator', () {
      expect(AdjectivalGrade.e4 > AdjectivalGrade.e3, isTrue);
      expect(AdjectivalGrade.e3 > AdjectivalGrade.e2, isTrue);
      expect(AdjectivalGrade.e2 > AdjectivalGrade.e1, isTrue);
      expect(AdjectivalGrade.e1 > AdjectivalGrade.e0, isTrue);
      expect(AdjectivalGrade.e2 > AdjectivalGrade.e2, isFalse);
      expect(AdjectivalGrade.e1 > AdjectivalGrade.e2, isFalse);
    });

    test('less than operator', () {
      expect(AdjectivalGrade.e0 < AdjectivalGrade.e1, isTrue);
      expect(AdjectivalGrade.e1 < AdjectivalGrade.e2, isTrue);
      expect(AdjectivalGrade.e2 < AdjectivalGrade.e3, isTrue);
      expect(AdjectivalGrade.e3 < AdjectivalGrade.e4, isTrue);
      expect(AdjectivalGrade.e3 < AdjectivalGrade.e3, isFalse);
      expect(AdjectivalGrade.e4 < AdjectivalGrade.e3, isFalse);
    });

    test('greater than or equal operator', () {
      expect(AdjectivalGrade.e4 >= AdjectivalGrade.e3, isTrue);
      expect(AdjectivalGrade.e3 >= AdjectivalGrade.e3, isTrue);
      expect(AdjectivalGrade.e2 >= AdjectivalGrade.e3, isFalse);
    });

    test('less than or equal operator', () {
      expect(AdjectivalGrade.e1 <= AdjectivalGrade.e2, isTrue);
      expect(AdjectivalGrade.e2 <= AdjectivalGrade.e2, isTrue);
      expect(AdjectivalGrade.e3 <= AdjectivalGrade.e2, isFalse);
    });
  });
}
