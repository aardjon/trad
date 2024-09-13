///
/// Definition of the boundary between storage adapters (`adapters` ring) and a concrete repository
/// implementation (`infrastructure` ring).
///
library;

/// Boundary interface to a key-value store.
///
/// A key-value store is a repository organizing data in simple key+value pairs.
///
/// This interface provides generic access to such a key-value database. The key-value database must
/// be initialized by calling [initialize] prior to any other calls. If the database is
/// uninitialized, all other methods will throw a [StateError].
abstract interface class KeyValueStoreBoundary {
  /// Initializes the key-value store for this application.
  ///
  /// This establishes a connection and creates a new, empty storage database if there is no
  /// existing one already. Must be called prior to any other operations.
  Future<void> initialize();

  /// Store the given integer [value] to the [key].
  ///
  /// Throws [StateError] if [initialize] has not been called (or failed).
  Future<bool> setInt({required String key, required int value});

  /// Store the given boolean [value] to the [key].
  ///
  /// Throws [StateError] if [initialize] has not been called (or failed).
  Future<bool> setBool({required String key, required bool value});

  /// Store the given double [value] to the [key].
  ///
  /// Throws [StateError] if [initialize] has not been called (or failed).
  Future<bool> setDouble({required String key, required double value});

  /// Store the given String [value] to the [key].
  ///
  /// Throws [StateError] if [initialize] has not been called (or failed).
  Future<bool> setString({required String key, required String value});

  /// Store the given string list [value] to the [key].
  ///
  /// Throws [StateError] if [initialize] has not been called (or failed).
  Future<bool> setStringList({required String key, required List<String> value});

  /// Store the given enum [value] to the [key].
  ///
  /// Throws [StateError] if [initialize] has not been called (or failed).
  Future<bool> setEnum({required String key, required Enum value});

  /// Retrieve the integer value stored for the requested [key].
  ///
  /// Returns null if there is no value stored for the requested key.
  /// Throws:
  ///  - [TypeError]: The [key] exists but its value is of a different type
  ///  - [StateError]: [initialize] has not been called (or failed)
  Future<int?> getInt(String key);

  /// Retrieve the boolean value stored for the requested [key].
  ///
  /// Returns null if there is no value stored for the requested key.
  /// Throws:
  ///  - [TypeError]: The [key] exists but its value is of a different type
  ///  - [StateError]: [initialize] has not been called (or failed)
  Future<bool?> getBool(String key);

  /// Retrieve the double value stored for the requested [key].
  ///
  /// Returns null if there is no value stored for the requested key.
  /// Throws:
  ///  - [TypeError]: The [key] exists but its value is of a different type
  ///  - [StateError]: [initialize] has not been called (or failed)
  Future<double?> getDouble(String key);

  /// Retrieve the String value stored for the requested [key].
  ///
  /// Returns null if there is no value stored for the requested key.
  /// Throws:
  ///  - [TypeError]: The [key] exists but its value is of a different type
  ///  - [StateError]: [initialize] has not been called (or failed)
  Future<String?> getString(String key);

  /// Retrieve the string list value stored for the requested [key].
  ///
  /// Returns null if there is no value stored for the requested key.
  /// Throws:
  ///  - [TypeError]: The [key] exists but its value is of a different type
  ///  - [StateError]: [initialize] has not been called (or failed)
  Future<List<String>?> getStringList(String key);

  /// Retrieve the enum value stored for the requested [key].
  ///
  /// Returns null if there is no value stored for the requested key or the value cannot be mapped
  /// to one of the enum values.
  /// Throws:
  ///  - [TypeError]: The [key] exists but its value is of a different type
  ///  - [StateError]: [initialize] has not been called (or failed)
  Future<T?> getEnum<T extends Enum>(String key, List<T> enumValues);
}
