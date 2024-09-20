///
/// Library providing the component interface for encapsulating file system access.
///
library;

import 'dart:core';
import 'dart:io';

/// Interface providing access to the file system.
///
/// This boundary provides [File] and [Directory] instances that can be used within the `adapters`
/// and `infrastructure` rings. Never instantiate them by yourself, to allow for easier testing by
/// mocking the file system! Furthermore, this boundary provides methods for manipulating or
/// creating path strings.
///
/// All input path strings must be valid local paths on the current platform.
abstract interface class FileSystemBoundary {
  /// Returns a new [File] instance representing the file under the given [filePath].
  File getFile(String filePath);

  /// Returns a new [Directory] instance representing the directory under the given [directoryPath].
  Directory getDirectory(String directoryPath);

  /// Joins the given [basePath] path with [appendPath] by appending the latter to the former and
  /// returns the normalized result.
  ///
  /// Both paths must be valid paths for the current platform (they do not have to exist, though).
  /// [appendPath] must not be an absolute path.
  ///
  /// Throws an ArgumentError if any of the given parameters is invalid (e.g. empty String or
  /// absolute [appendPath].
  String joinPaths(String basePath, String appendPath);

  /// Appends the given path [parts] to [basePath] and returns the normalized result.
  ///
  /// [basePath] must be a valid path for the current platform (it does not have to exist, though).
  /// [parts] must be a non-empty iterable of path elements ot be added, each element being a
  /// directory or file name. They must not contain path separators (i.e. `/` or `\`).
  ///
  /// Throws an ArgumentError if any of the given parameters is invalid (e.g. empty [parts]).
  String joinPathParts(String basePath, List<String> parts);
}
