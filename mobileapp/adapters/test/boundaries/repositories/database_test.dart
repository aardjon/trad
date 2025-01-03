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
    const String optBoolColumnName = 'opt_bool_column';
    const String intColumnName = 'int_column';
    const String optIntColumnName = 'opt_int_column';
    const String doubleColumnName = 'double_column';
    const String optDoubleColumnName = 'opt_double_column';
    const String stringColumnName = 'string_column';
    const String optStringColumnName = 'opt_string_column';

    const Map<String, Object?> expectedValues = <String, Object?>{
      boolColumnName: true,
      optBoolColumnName: null,
      intColumnName: 42,
      optIntColumnName: null,
      doubleColumnName: 13.37,
      optDoubleColumnName: null,
      stringColumnName: 'Lorem Ipsum!',
      optStringColumnName: null,
    };

    /// Ensures that available values can be retrieved.
    test('test existing values', () {
      ResultRow row = ResultRow(expectedValues);
      expect(row.getStringValue(stringColumnName), equals(expectedValues[stringColumnName]));
      expect(
        row.getOptStringValue(optStringColumnName),
        equals(expectedValues[optStringColumnName]),
      );
      expect(row.getIntValue(intColumnName), equals(expectedValues[intColumnName]));
      expect(row.getOptIntValue(optIntColumnName), equals(expectedValues[optIntColumnName]));
      expect(row.getDoubleValue(doubleColumnName), equals(expectedValues[doubleColumnName]));
      expect(
        row.getOptDoubleValue(optDoubleColumnName),
        equals(expectedValues[optDoubleColumnName]),
      );
      expect(row.getBoolValue(boolColumnName), equals(expectedValues[boolColumnName]));
      expect(row.getOptBoolValue(optBoolColumnName), equals(expectedValues[optBoolColumnName]));
    });

    /// Ensures that missing values cannot be retrieved (an Error shall be thrown).
    test('test non-existing values', () {
      ResultRow row = ResultRow(expectedValues);
      expect(() => row.getStringValue('doesnotexist'), throwsArgumentError);
      expect(() => row.getOptStringValue('doesnotexist'), throwsArgumentError);
      expect(() => row.getIntValue('doesnotexist'), throwsArgumentError);
      expect(() => row.getOptIntValue('doesnotexist'), throwsArgumentError);
      expect(() => row.getDoubleValue('doesnotexist'), throwsArgumentError);
      expect(() => row.getOptDoubleValue('doesnotexist'), throwsArgumentError);
      expect(() => row.getBoolValue('doesnotexist'), throwsArgumentError);
      expect(() => row.getOptBoolValue('doesnotexist'), throwsArgumentError);
    });

    /// Ensures that requesting a value of the wrong type throws an Error.
    test('test invalid type', () {
      ResultRow row = ResultRow(expectedValues);
      expect(() => row.getStringValue(intColumnName), throwsA(isA<TypeError>()));
      expect(() => row.getOptStringValue(intColumnName), throwsA(isA<TypeError>()));
      expect(() => row.getStringValue(optIntColumnName), throwsA(isA<TypeError>()));

      expect(() => row.getIntValue(boolColumnName), throwsA(isA<TypeError>()));
      expect(() => row.getOptIntValue(boolColumnName), throwsA(isA<TypeError>()));
      expect(() => row.getIntValue(optBoolColumnName), throwsA(isA<TypeError>()));

      expect(() => row.getDoubleValue(stringColumnName), throwsA(isA<TypeError>()));
      expect(() => row.getOptDoubleValue(stringColumnName), throwsA(isA<TypeError>()));
      expect(() => row.getDoubleValue(optStringColumnName), throwsA(isA<TypeError>()));

      expect(() => row.getBoolValue(doubleColumnName), throwsA(isA<TypeError>()));
      expect(() => row.getOptBoolValue(doubleColumnName), throwsA(isA<TypeError>()));
      expect(() => row.getBoolValue(optDoubleColumnName), throwsA(isA<TypeError>()));
    });
  });
}
