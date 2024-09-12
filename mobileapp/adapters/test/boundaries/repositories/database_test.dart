///
/// Unit tests for the adapters.boundaries.repositories.database library.
///
library;

import 'package:test/test.dart';

import 'package:adapters/boundaries/repositories/database.dart';

void main() {
  /// Unit tests for the adapters.boundaries.repositories.database.ResultRow class.
  group('adapters.boundaries.repositories.database.ResultRow', () {
    const String boolColumnName = 'bool_column';
    const String intColumnName = 'int_column';
    const String doubleColumnName = 'double_column';
    const String stringColumnName = 'string_column';

    const Map<String, Object> expectedValues = <String, Object>{
      boolColumnName: true,
      intColumnName: 42,
      doubleColumnName: 13.37,
      stringColumnName: 'Lorem Ipsum!',
    };

    /// Ensures that available values can be retrieved.
    test('test existing values', () {
      ResultRow row = ResultRow(expectedValues);
      expect(row.getStringValue(stringColumnName), equals(expectedValues[stringColumnName]));
      expect(row.getIntValue(intColumnName), equals(expectedValues[intColumnName]));
      expect(row.getDoubleValue(doubleColumnName), equals(expectedValues[doubleColumnName]));
      expect(row.getBoolValue(boolColumnName), equals(expectedValues[boolColumnName]));
    });

    /// Ensures that missing values cannot be retrieved (an Error shall be thrown).
    test('test non-existing values', () {
      ResultRow row = ResultRow(expectedValues);
      expect(() => row.getStringValue('doesnotexist'), throwsArgumentError);
      expect(() => row.getIntValue('doesnotexist'), throwsArgumentError);
      expect(() => row.getDoubleValue('doesnotexist'), throwsArgumentError);
      expect(() => row.getBoolValue('doesnotexist'), throwsArgumentError);
    });

    /// Ensures that requesting a value of the wrong type throws an Error.
    test('test invalid type', () {
      ResultRow row = ResultRow(expectedValues);
      expect(() => row.getStringValue(intColumnName), throwsA(isA<TypeError>()));
      expect(() => row.getIntValue(boolColumnName), throwsA(isA<TypeError>()));
      expect(() => row.getDoubleValue(stringColumnName), throwsA(isA<TypeError>()));
      expect(() => row.getBoolValue(doubleColumnName), throwsA(isA<TypeError>()));
    });
  });
}
