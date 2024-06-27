///
/// Library providing a single journal entry
///
library;

import 'package:meta/meta.dart';

import 'adjectival_grade.dart';
import 'technical_grade.dart';

/// Uniquely identifies a single journal entry.
///
/// The exact value is undetermined and depends on the concrete storage implementation. The only
/// operations that are guaranteed on IDs are:
///  - Compare for (in)equality
///  - Convert to String (e.g. for printing/logging)
typedef JournalEntryId = String;

/// Represents a single journal entry
@immutable
class JournalEntry {
  /// Unique id of this journal entry
  final JournalEntryId? identifier;

  /// Date of the entry
  final DateTime date;

  /// Area of the entry
  final String area;

  /// Summit of the entry
  final String summit;

  /// Route of the entry
  final String route;

  /// Technical grade of the route
  final TechnicalGrade technicalGrade;

  /// Optional adjectival grade of the route
  final AdjectivalGrade? adjectivalGrade;

  /// Optional notes for the entry
  final String? note;

  /// Constructor for directly initializing all members.
  const JournalEntry(
    this.identifier,
    this.date,
    this.area,
    this.summit,
    this.route,
    this.technicalGrade,
    this.adjectivalGrade,
    this.note,
  );

  @override
  bool operator ==(Object other) {
    if (identical(this, other)) return true;

    return other is JournalEntry &&
        other.identifier == identifier &&
        other.date == date &&
        other.area == area &&
        other.summit == summit &&
        other.route == route &&
        other.technicalGrade == technicalGrade &&
        other.adjectivalGrade == adjectivalGrade &&
        other.note == note;
  }

  @override
  int get hashCode {
    return identifier.hashCode ^
        date.hashCode ^
        area.hashCode ^
        summit.hashCode ^
        route.hashCode ^
        technicalGrade.hashCode ^
        adjectivalGrade.hashCode ^
        note.hashCode;
  }
}
