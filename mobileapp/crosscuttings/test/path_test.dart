///
/// Unit tests for the crosscuttings.path library.
///
library;

import 'dart:io';

import 'package:crosscuttings/path.dart';
import 'package:path/path.dart' as pathlib;
import 'package:test/test.dart';

/// Unit tests for the crosscuttings.path.Path class.
void main() {
  /// Ensure the correct behaviour of the Path.toString() with different construction values:
  ///  - Without argument, it points to the current working directory
  ///  - A relative path is based on the current working dir
  ///  - An absolute path is taken as-is
  ///  - toString() returns an absolute, normalized path in all cases (i.e. .. and . parts are
  ///    removed)
  test('crosscuttings.path.testStringSerializsation', () {
    final String currentWorkingDir = pathlib.absolute(pathlib.current);
    final String relativePath = pathlib.join('subdir', 'file.txt');
    final String absolutePath =
        Platform.isWindows ? r'C:\Documents\file.dart' : '/home/user/project/file.dart';
    final String unnormalizedPath = pathlib.join('subdir', '.', 'subsubdir', '..', 'file.txt');

    expect(Path().toString(), equals(currentWorkingDir));
    expect(Path(relativePath).toString(), equals(pathlib.join(currentWorkingDir, relativePath)));
    expect(Path(absolutePath).toString(), equals(absolutePath));
    expect(
      Path(unnormalizedPath).toString(),
      equals(pathlib.join(currentWorkingDir, relativePath)),
    );
  });

  /// Ensure the correct behaviour of the Path.toUri() with different construction values:
  ///  - Without argument, it points to the current working directory
  ///  - A relative path is based on the current working dir
  ///  - An absolute path is taken as-is
  test('crosscuttings.path.testUriSerializsation', () {
    final String currentWorkingDir = pathlib.absolute(pathlib.current);
    final String relativePath = pathlib.join('subdir', 'file.txt');
    final String absolutePath =
        Platform.isWindows ? r'C:\Documents\file.dart' : '/home/user/project/file.dart';

    expect(Path().toUri().toString(), equals('file://$currentWorkingDir'));
    expect(
      Path(relativePath).toUri().toString(),
      equals('file://${pathlib.join(currentWorkingDir, relativePath)}'),
    );
    expect(Path(absolutePath).toUri().toString(), equals('file://$absolutePath'));
  });

  test('crosscuttings.path.testJoin', () {
    final String currentWorkingDir = pathlib.absolute(pathlib.current);
    final String relativePath = pathlib.join('subdir', 'file.txt');

    expect(
      Path().join(relativePath).toString(),
      equals(pathlib.join(currentWorkingDir, relativePath)),
    );
  });
}
