///
/// Unit tests for the infrastructure_vanilla.repositories.dartio_path component.
///
library;

import 'package:path/path.dart' show Context, posix, windows;
import 'package:test/test.dart';

import 'package:infrastructure_vanilla/repositories/dartio_path.dart';

/// Parameters for a single `joinPaths` test case:
/// $1: The `path` Context to use
/// $2: The platform name ("Windows" or "Posix")
/// $3: Platform specific, absolute base path
/// $4: Platform specific, absolute expected result path
typedef _PlatformPathTestParameters = (
  Context,
  String,
  String,
  String,
);

/// Unit tests for the infrastructure_vanilla.dartio_path.DartIoFileSystem class.
void main() {
  /// Ensures that the object returned by `getFile()` points to the given path.
  test('infrastructure_vanilla.dartio_path.DartIoFileSystem.getFile()', () {
    DartIoFileSystem filesystem = DartIoFileSystem();
    const String filePath = '/path/to/file.txt';
    expect(filesystem.getFile(filePath).path, equals(filePath));
  });

  /// Ensures that the object returned by `getDirectory()` points to the given path.
  test('infrastructure_vanilla.dartio_path.DartIoFileSystem.getDirectory()', () {
    DartIoFileSystem filesystem = DartIoFileSystem();
    const String directoryPath = '/path/to/dir';
    expect(filesystem.getDirectory(directoryPath).path, equals(directoryPath));
  });

  /// Tests the correct behaviour of the joinPaths method:
  ///  - A relative second argument is always appended correctly
  ///  - An absolute second argument causes an ArgumentError to be thrown
  ///  - An empty string causes an ArgumentError to be thrown
  group('joinPath', () {
    List<_PlatformPathTestParameters> testParameters = <_PlatformPathTestParameters>[
      (posix, 'Posix', '/home/user/', '/home/user/example.txt'),
      (windows, 'Windows', r'C:\Documents\', r'C:\Documents\example.txt'),
    ];

    for (final _PlatformPathTestParameters parameters in testParameters) {
      test(parameters.$2, () {
        final String absBasePath = parameters.$3;
        const String joinFilename = 'example.txt';
        final String expectedResult = parameters.$4;

        DartIoFileSystem filesystem = DartIoFileSystem(pathContext: parameters.$1);

        // Test normal case
        expect(filesystem.joinPaths(absBasePath, joinFilename), equals(expectedResult));
        // Ensure exceptions for empty arguments
        expect(() => filesystem.joinPaths('', joinFilename), throwsArgumentError);
        expect(() => filesystem.joinPaths(absBasePath, ''), throwsArgumentError);
        expect(() => filesystem.joinPaths('', ''), throwsArgumentError);
        // Ensure exception for absolute second path
        expect(() => filesystem.joinPaths(absBasePath, absBasePath), throwsArgumentError);
      });
    }
  });

  /// Tests the correct behaviour of the joinPathParts method:
  ///  - All parts must be appended to the basePath
  ///  - Without any parts, an ArgumentError is thrown
  ///  - An empty base path string causes an ArgumentError to be thrown
  group('joinPathParts', () {
    List<_PlatformPathTestParameters> testParameters = <_PlatformPathTestParameters>[
      (posix, 'Posix', '/home/user/', '/home/user/subdir/example.txt'),
      (windows, 'Windows', r'C:\Documents', r'C:\Documents\subdir\example.txt'),
    ];
    for (final _PlatformPathTestParameters parameters in testParameters) {
      test(parameters.$2, () {
        final String absBasePath = parameters.$3;
        const List<String> parts = <String>['subdir', 'example.txt'];
        final String expectedResult = parameters.$4;

        DartIoFileSystem filesystem = DartIoFileSystem(pathContext: parameters.$1);

        // Test normal case
        expect(filesystem.joinPathParts(absBasePath, parts), equals(expectedResult));
        // Ensure exception for empty base path
        expect(() => filesystem.joinPathParts('', parts), throwsArgumentError);
        // Ensure exception for missing parts
        expect(() => filesystem.joinPathParts(absBasePath, <String>[]), throwsArgumentError);
      });
    }
  });
}
