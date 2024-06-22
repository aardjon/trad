///
/// Unit tests for the technical grade library.
///
library;

import 'package:test/test.dart';

import 'package:core/entities/technical_grade.dart';

/// Unit tests for the technical grade enum.
void main() {
  group('technicalGrade', () {
    
    test('toString returns correct caption', () {
      Map<TechnicalGrade, String> expected = <TechnicalGrade, String> {
        TechnicalGrade.i: 'I',
        TechnicalGrade.ii: 'II',
        TechnicalGrade.iii: 'III',
        TechnicalGrade.iv: 'IV',
        TechnicalGrade.v: 'V',
        TechnicalGrade.vi: 'VI',
        TechnicalGrade.viia: 'VIIa',
        TechnicalGrade.viib: 'VIIb',
        TechnicalGrade.viic: 'VIIc',
        TechnicalGrade.viiia: 'VIIIa',
        TechnicalGrade.viiib: 'VIIIb',
        TechnicalGrade.viiic: 'VIIIc',
        TechnicalGrade.ixa: 'IXa',
        TechnicalGrade.ixb: 'IXb',
        TechnicalGrade.ixc: 'IXc',
        TechnicalGrade.xa: 'Xa',
        TechnicalGrade.xb: 'Xb',
        TechnicalGrade.xc: 'Xc',
        TechnicalGrade.xia: 'XIa',
        TechnicalGrade.xib: 'XIb',
        TechnicalGrade.xic: 'XIc',
        TechnicalGrade.xiia: 'XIIa',
        TechnicalGrade.xiib: 'XIIb',
        TechnicalGrade.xiic: 'XIIc',
        TechnicalGrade.xiiia: 'XIIIa',
        TechnicalGrade.xiiib: 'XIIIb',
        TechnicalGrade.xiiic: 'XIIIc',
        TechnicalGrade.jump1: '1',
        TechnicalGrade.jump2: '2',
        TechnicalGrade.jump3: '3',
        TechnicalGrade.jump4: '4',
        TechnicalGrade.jump5: '5',
        TechnicalGrade.jump6: '6',
        TechnicalGrade.jump7: '7',
      };

      expected.forEach((TechnicalGrade technicalGrade, String exectedString) {
        String actualString = technicalGrade.toString();
        expect(actualString, exectedString);
      });      
    });

    test('greater than operator', () {
      expect(TechnicalGrade.viib > TechnicalGrade.viia, isTrue);
      expect(TechnicalGrade.vi > TechnicalGrade.v, isTrue);
      expect(TechnicalGrade.jump3 > TechnicalGrade.jump1, isTrue);
      expect(TechnicalGrade.vi > TechnicalGrade.vi, isFalse);
      expect(TechnicalGrade.v > TechnicalGrade.vi, isFalse);                     
    });      
    
    test('less than operator', () {
      expect(TechnicalGrade.jump2 < TechnicalGrade.jump4, isTrue);
      expect(TechnicalGrade.xia < TechnicalGrade.xic, isTrue);
      expect(TechnicalGrade.v < TechnicalGrade.vi, isTrue);
      expect(TechnicalGrade.vi < TechnicalGrade.vi, isFalse);
      expect(TechnicalGrade.vi < TechnicalGrade.v, isFalse);
    });

    test('greater than or equal operator', () {
      expect(TechnicalGrade.vi >= TechnicalGrade.v, isTrue);
      expect(TechnicalGrade.vi >= TechnicalGrade.vi, isTrue);
      expect(TechnicalGrade.v >= TechnicalGrade.vi, isFalse);
    });

    test('less than or equal operator', () {
      expect(TechnicalGrade.v <= TechnicalGrade.vi, isTrue);
      expect(TechnicalGrade.vi <= TechnicalGrade.vi, isTrue);
      expect(TechnicalGrade.vi <= TechnicalGrade.v, isFalse);
    });
  });    
}
