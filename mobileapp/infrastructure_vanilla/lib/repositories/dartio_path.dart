///
/// dart:io/path implementation of the [FileSystemBoundary] repository.
///
library;

import 'dart:io';

import 'package:path/path.dart' show Context, context;

import 'package:adapters/boundaries/repositories/filesystem.dart';

/// dart:io based implementation for accessing the local file system.
///
/// This implementation serves two purposes:
/// 1. It encapsulates the `path` package for modifying (e.g. joining) path strings. This allows to
/// easily replace or update this external dependency in the future if necessary.
/// 2. It provides `FileSystemEntity` (dart:io) objects that can be used to access the local file
/// system. This allows to replace/mock the actually used file system implementation e.g. for unit
/// tests, without requiring us to reinvent the whole IO API.
class DartIoFileSystem implements FileSystemBoundary {
  /// Platform context for creating/manipulation path strings.
  ///
  /// This handles e.g. the correct path separator. Always use this context to access the `path`
  /// library, don't use the global functions from there directly!
  final Context _context;

  /// Constructor for injecting an alternative platform context.
  ///
  /// For unit testing different platform behaviour, an alternative `path` context can be injected
  /// by providing it as [pathContext]. In normal/productive cases always use the default parameter
  /// value (which uses the current platform's context).
  DartIoFileSystem({Context? pathContext}) : _context = pathContext ?? context;

  @override
  File getFile(String filePath) {
    return File(filePath);
  }

  @override
  Directory getDirectory(String directoryPath) {
    return Directory(directoryPath);
  }

  @override
  String joinPaths(String basePath, String appendPath) {
    if (basePath.isEmpty) {
      throw ArgumentError('Cannot join with an empty base path');
    }
    if (appendPath.isEmpty) {
      throw ArgumentError('Cannot append empty path');
    }
    if (_context.isAbsolute(appendPath)) {
      throw ArgumentError('Cannot append an absolute path');
    }
    return _context.join(basePath, appendPath);
  }

  @override
  String joinPathParts(String basePath, Iterable<String> parts) {
    if (basePath.isEmpty) {
      throw ArgumentError('Cannot join with an empty base path');
    }
    String appendPath = _context.joinAll(parts);
    return joinPaths(basePath, appendPath);
  }
}
