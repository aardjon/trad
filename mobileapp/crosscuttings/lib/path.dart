///
/// Library for encapsulating Dart's `path` package behind a nice OOP interface.
///
library;

import 'package:path/path.dart' as pathlib;

/// Represents a certain location within the (local) file system.
///
/// In instance of this class uniquely identifies a certain file system location and allows some
/// basic path manipulation operations that can be useful everywhere (including the core). It does
/// not provide file system operations because this is limited to the outer rings, though.
///
/// [Path] instances cannot be modified, all modifying operations return a new [Path] instance
/// instead.
///
/// This class basically wraps the `path` package (https://pub.dev/packages/path) so that only one
/// place needs to be adapted in case of incompatible upstream changes. As a side effect, it
/// provides a nicer, object-oriented path interface (which is somewhat inspired from Pythons
/// `pathlib` module).
class Path {
  final String _absolutePath;

  /// Creates a new Path instance from the given [pathStr].
  ///
  /// The given path does not have to exist, but it must be a valid (absolute or relative) path for
  /// the current platform. A relative [pathStr] is assumed to be relative to the current working
  /// directory. If [pathStr] is missing, the resulting Path instance points to the current working
  /// directory.
  Path([String? pathStr])
      : _absolutePath = pathStr == null
            ? pathlib.normalize(pathlib.absolute(pathlib.current))
            : pathlib.normalize(pathlib.absolute(pathStr));

  @override
  String toString() {
    return _absolutePath;
  }

  /// Returns a URI pointing the the same location as `this`.
  ///
  /// The returned URI is always a `file://` URI, of course.
  Uri toUri() {
    return pathlib.toUri(_absolutePath);
  }

  /// Join this instance with the given [other] path by appending the latter to the former.
  Path join(String other) {
    return Path(pathlib.join(_absolutePath, other));
  }
}
