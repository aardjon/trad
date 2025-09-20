///
/// Unit tests for the trad.core.entities.errors library.
///
/// The tested module contains Error/Exception classes only. The main goal of their unit tests is
/// to ensure that all relevant information is contained in the exception's string representation
/// when using toString(), because this string is usually logged in case of problems.
///
library;

import 'package:core/entities/errors.dart';
import 'package:test/test.dart';

void main() {
  const String dummyConnectionString = 'file://dummy/db/path.sqlite';

  test('StorageStartingException', () {
    String message = StorageStartingException(dummyConnectionString).toString();
    expect(message, contains(dummyConnectionString));
  });

  test('InaccessibleStorageException', () {
    final Exception nestedError = Exception('Nested Error');
    String message = InaccessibleStorageException(dummyConnectionString, nestedError).toString();
    expect(message, contains(dummyConnectionString));
    expect(message, contains(nestedError.toString()));
  });

  test('InvalidStorageFormatException', () {
    const String errorMessage = 'Fake Error';
    String message = InvalidStorageFormatException(dummyConnectionString, errorMessage).toString();
    expect(message, contains(dummyConnectionString));
    expect(message, contains(errorMessage));
  });

  test('IncompatibleStorageException', () {
    const String requiredVersion = '3.2';
    const String actualVersion = '2.0';
    String message = IncompatibleStorageException(
      dummyConnectionString,
      actualVersion,
      requiredVersion,
    ).toString();
    expect(message, contains(dummyConnectionString));
    expect(message, contains(requiredVersion));
    expect(message, contains(actualVersion));
  });
}
