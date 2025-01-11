///
/// Exception types that can be thrown by storage components (trad.core.boundaries.storage) when
/// they encounter any runtime problems.
///
library;

/// Generic base type for all exception thrown when starting/opening a storage fails.
class StorageStartingException implements Exception {
  /// The connection string of the storage that failed to start.
  final String connectionString;

  /// Constructor for directly initializing all members.
  StorageStartingException(this.connectionString);

  @override
  String toString() {
    return 'StorageStartingException: $connectionString';
  }
}

/// Thrown when starting a storage fails because it is not accessible.
///
/// This can be caused by things like e.g.
///  - Non-existing files
///  - Permission problems
///  - Resource (e.g. lock or quote/limits) problems
class InaccessibleStorageException extends StorageStartingException {
  /// The original Exception caught within the storage component.
  final Exception accessError;

  /// Constructor for directly initializing all members.
  InaccessibleStorageException(super.connectionString, this.accessError);

  @override
  String toString() {
    return 'InaccessibleStorageException: $accessError ($connectionString)';
  }
}

/// Thrown when a storage resource exists but is of an unexpected format.
///
/// This is the typical "expected a text file, got a JPEG" case.
class InvalidStorageFormatException extends StorageStartingException {
  /// An error message containing some more details about the problem (not meant to be displayed to
  /// users).
  final String message;

  /// Constructor for directly initializing all members.
  InvalidStorageFormatException(super.connectionString, this.message);

  @override
  String toString() {
    return 'InvalidStorageFormatException: $message ($connectionString)';
  }
}

/// Thrown when the storage uses an incompatible content format version.
///
/// This is typically caused after up- or downgrading the app to a version which uses a newer or
/// older content schema.
class IncompatibleStorageException extends StorageStartingException {
  /// Version identifier of the storage that failed to be started.
  final Object storageVersion;

  /// Identifier of the version required by this app.
  final Object requiredVersion;

  /// Constructor for directly initializing all members.
  IncompatibleStorageException(super.connectionString, this.storageVersion, this.requiredVersion);

  @override
  String toString() {
    return 'IncompatibleStorageException: $storageVersion != $requiredVersion ($connectionString)';
  }
}
