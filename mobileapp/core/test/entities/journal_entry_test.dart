///
/// Unit tests for the journal entry library.
///
library;

import 'package:test/test.dart';

import 'package:core/entities/adjectival_grade.dart';
import 'package:core/entities/technical_grade.dart';
import 'package:core/entities/journal_entry.dart';

/// Unit tests for the journal entry class.
void main() {
  group('journalEntry', () {
    test('equal operator', () {
      JournalEntry entry1 = JournalEntry(
        '1',
        DateTime(2024, 06, 22),
        'Bielatal',
        'Daxenstein',
        'AW',
        TechnicalGrade.i,
        null,
        'Auf Seilzug achten',
      );

      JournalEntry entry2 = entry1;

      JournalEntry entry3 = JournalEntry(
        '1',
        DateTime(2024, 06, 22),
        'Bielatal',
        'Daxenstein',
        'AW',
        TechnicalGrade.i,
        null,
        'Auf Seilzug achten',
      );

      JournalEntry entry4 = JournalEntry(
        null,
        DateTime(2024, 06, 22),
        'Bielatal',
        'Daxenstein',
        'AW',
        TechnicalGrade.i,
        AdjectivalGrade.e1,
        'Auf Seilzug achten',
      );

      JournalEntry entry5 = JournalEntry(
        null,
        DateTime(2024, 06, 22),
        'Bielatal',
        'Daxenstein',
        'AW',
        TechnicalGrade.i,
        AdjectivalGrade.e1,
        'Auf Seilzug achten',
      );

      expect(entry1 == entry2, isTrue);
      expect(entry1 == entry3, isTrue);
      expect(entry1 == entry4, isFalse);
      expect(entry4 == entry5, isTrue);
    });
  });
}
