///
/// Library providing the adjectival grade.
///
library;

/// Represents the adjectival grades
enum AdjectivalGrade {     
  /// Can be optimally secured with rings and/or obvious slings.
  e0('E0'),
  /// Can be secured extremely well with the existing rings and/or slings.
  e1('E1'),
  /// The Saxon norm.
  e2('E2'),
  /// Rather moderately secure by Saxon standards.
  e3('E3'),
  /// Cannot be properly secured.
  e4('E4');

  const AdjectivalGrade(this.caption);

  /// Caption of the technical grade
  final String caption;

  /// Greater than operator
  bool operator >(AdjectivalGrade other) => index > other.index; 

  /// Less than operator
  bool operator <(AdjectivalGrade other) => index < other.index;

  /// Greater than or equal operator
  bool operator >=(AdjectivalGrade other) => index >= other.index;

  /// Less than or equal operator
  bool operator <=(AdjectivalGrade other) => index <= other.index;

  @override
  String toString() => caption;  
}
