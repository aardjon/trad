///
/// Library providing the technical grade.
///
library;

/// Represents the technical grades
enum TechnicalGrade {
  /// Climbing grade I
  i('I'),

  /// Climbing grade II
  ii('II'),

  /// Climbing grade III
  iii('III'),

  /// Climbing grade IV
  iv('IV'),

  /// Climbing grade V
  v('V'),

  /// Climbing grade VI
  vi('VI'),

  /// Climbing grade VIIa
  viia('VIIa'),

  /// Climbing grade VIIb
  viib('VIIb'),

  /// Climbing grade VIIc
  viic('VIIc'),

  /// Climbing grade VIIIa
  viiia('VIIIa'),

  /// Climbing grade VIIIb
  viiib('VIIIb'),

  /// Climbing grade VIIIc
  viiic('VIIIc'),

  /// Climbing grade IXa
  ixa('IXa'),

  /// Climbing grade IXb
  ixb('IXb'),

  /// Climbing grade IXc
  ixc('IXc'),

  /// Climbing grade Xa
  xa('Xa'),

  /// Climbing grade Xb
  xb('Xb'),

  /// Climbing grade Xc
  xc('Xc'),

  /// Climbing grade XIa
  xia('XIa'),

  /// Climbing grade XIb
  xib('XIb'),

  /// Climbing grade XIc
  xic('XIc'),

  /// Climbing grade XIIa
  xiia('XIIa'),

  /// Climbing grade XIIb
  xiib('XIIb'),

  /// Climbing grade XIIc
  xiic('XIIc'),

  /// Climbing grade XIIa
  xiiia('XIIIa'),

  /// Climbing grade XIIb
  xiiib('XIIIb'),

  /// Climbing grade XIIc
  xiiic('XIIIc'),

  /// Jump grade 1
  jump1('1'),

  /// Jump grade 2
  jump2('2'),

  /// Jump grade 3
  jump3('3'),

  /// Jump grade 4
  jump4('4'),

  /// Jump grade 5
  jump5('5'),

  /// Jump grade 6
  jump6('6'),

  /// Jump grade 7
  jump7('7');

  const TechnicalGrade(this.caption);

  /// Caption of the technical grade
  final String caption;

  /// Greater than operator
  bool operator >(TechnicalGrade other) => index > other.index;

  /// Less than operator
  bool operator <(TechnicalGrade other) => index < other.index;

  /// Greater than or equal operator
  bool operator >=(TechnicalGrade other) => index >= other.index;

  /// Less than or equal operator
  bool operator <=(TechnicalGrade other) => index <= other.index;

  @override
  String toString() => caption;
}
