///
/// Definition of the boundary between storage adapters (`adapters` ring) and a concrete repository
/// implementation (`infrastructure` ring).
///
library;

/// Boundary interface to a key-value store.
///
/// A key-value store is a repository organizing data in simple key+value pairs-
/// This interface provides generic access to such a key-value database.
abstract interface class KeyValueStoreBoundary {
  /// Initializes the key-value store for this application.
  ///
  /// This establishes a connection and creates a new, empty storage database if there is no
  /// existing one already.
  Future<void> initialize();

  /// Store the given integer [value] to the [key].
  Future<bool> setInt({required String key, required int value});

  /// Store the given boolean [value] to the [key].
  Future<bool> setBool({required String key, required bool value});

  /// Store the given double [value] to the [key].
  Future<bool> setDouble({required String key, required double value});

  /// Store the given String [value] to the [key].
  Future<bool> setString({required String key, required String value});

  /// Store the given string list [value] to the [key].
  Future<bool> setStringList({required String key, required List<String> value});

  /// Store the given enum [value] to the [key].
  Future<bool> setEnum({required String key, required Enum value});

  /// Retrieve the integer value stored for the requested [key].
  ///
  /// Returns null if there is no value stored for the requested key, or if it is of a different
  /// type.
  Future<int?> getInt(String key);

  /// Retrieve the boolean value stored for the requested [key].
  ///
  /// Returns null if there is no value stored for the requested key, or if it is of a different
  /// type.
  Future<bool?> getBool(String key);

  /// Retrieve the double value stored for the requested [key].
  ///
  /// Returns null if there is no value stored for the requested key, or if it is of a different
  /// type.
  Future<double?> getDouble(String key);

  /// Retrieve the String value stored for the requested [key].
  ///
  /// Returns null if there is no value stored for the requested key, or if it is of a different
  /// type.
  Future<String?> getString(String key);

  /// Retrieve the string list value stored for the requested [key].
  ///
  /// Returns null if there is no value stored for the requested key, or if it is of a different
  /// type.
  Future<List<String>?> getStringList(String key);

  /// Retrieve the enum value stored for the requested [key].
  ///
  /// Returns null if there is no value stored for the requested key, or if it is of a different
  /// type.
  Future<T?> getEnum<T extends Enum>(String key, List<T> enumValues);
}
