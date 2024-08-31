///
/// Flutter & shared_preferences based implementation of a persisted key value store.
///
library;

import 'package:shared_preferences/shared_preferences.dart';

import 'package:adapters/boundaries/repositories/key_value_store.dart';

/// A key value store implementation that stores data as application preferences.
///
/// This is a wrapper implementation for the `shared_preferences` Flutter package.
class SharedPreferencesRepository implements KeyValueStoreBoundary {
  static SharedPreferences? _prefs;

  @override
  Future<void> initialize() async {
    await prefs;
  }

  Future<SharedPreferences?> get prefs async {
    _prefs ??= await SharedPreferences.getInstance();
    return _prefs;
  }

  @override
  Future<bool> setInt({required String key, required int value}) async {
    SharedPreferences? preferences = await prefs;
    return preferences!.setInt(key, value);
  }

  @override
  Future<bool> setBool({required String key, required bool value}) async {
    SharedPreferences? preferences = await prefs;
    return preferences!.setBool(key, value);
  }

  @override
  Future<bool> setDouble({required String key, required double value}) async {
    SharedPreferences? preferences = await prefs;
    return preferences!.setDouble(key, value);
  }

  @override
  Future<bool> setString({required String key, required String value}) async {
    SharedPreferences? preferences = await prefs;
    return preferences!.setString(key, value);
  }

  @override
  Future<bool> setStringList({required String key, required List<String> value}) async {
    SharedPreferences? preferences = await prefs;
    return preferences!.setStringList(key, value);
  }

  @override
  Future<bool> setEnum({required String key, required Enum value}) async {
    SharedPreferences? preferences = await prefs;
    return preferences!.setString(key, _enumToString(value));
  }

  @override
  Future<int?> getInt(String key) async {
    SharedPreferences? preferences = await prefs;
    return preferences!.getInt(key);
  }

  @override
  Future<bool?> getBool(String key) async {
    SharedPreferences? preferences = await prefs;
    return preferences!.getBool(key);
  }

  @override
  Future<double?> getDouble(String key) async {
    SharedPreferences? preferences = await prefs;
    return preferences!.getDouble(key);
  }

  @override
  Future<String?> getString(String key) async {
    SharedPreferences? preferences = await prefs;
    return preferences!.getString(key);
  }

  @override
  Future<List<String>?> getStringList(String key) async {
    SharedPreferences? preferences = await prefs;
    return preferences!.getStringList(key);
  }

  @override
  Future<T?> getEnum<T extends Enum>(String key, List<T> enumValues) async {
    SharedPreferences preferences = await SharedPreferences.getInstance();
    String? value = preferences.getString(key);
    return value == null ? null : _tryStringToEnum<T>(value, enumValues);
  }

  static String _enumToString(Enum value) {
    return value.name;
  }

  static T? _tryStringToEnum<T extends Enum>(String value, List<T> enumValues) {
    try {
      return enumValues.byName(value);
    } catch (e) {
      return null;
    }
  }
}
