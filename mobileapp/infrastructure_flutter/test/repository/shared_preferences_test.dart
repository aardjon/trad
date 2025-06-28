///
/// Unit tests for the infrastructure_flutter.repository.shared_preferences library.
///
library;

import 'package:shared_preferences/shared_preferences.dart';
import 'package:test/test.dart';

import 'package:infrastructure_flutter/repository/shared_preferences.dart';

enum DummyEnum1 { item1, item2 }

enum DummyEnum2 { item3, item4, item5 }

/// Unit tests for the repository.shared_preferences.SharedPreferencesRepository infrastructure
/// component, which implements the key_value_store interface as local application preferences.
void main() {
  tearDown(() {});

  group('infrastructure_flutter.repository.shared_preferences', () {
    /// Ensures that all methods throw an error if the repository is uninitialized (i.e.
    /// initialize() has not been called).
    test('uninitialized state', () async {
      // Create but don't initialize the repository instance, mocking the shared_preferences store
      // with an empty in-memory one.
      SharedPreferences.setMockInitialValues(<String, Object>{});
      SharedPreferencesRepository repository = SharedPreferencesRepository();

      expect(() async {
        await repository.getBool('key');
      }, throwsStateError);
      expect(() async {
        await repository.getInt('key');
      }, throwsStateError);
      expect(() async {
        await repository.getDouble('key');
      }, throwsStateError);
      expect(() async {
        await repository.getString('key');
      }, throwsStateError);
      expect(() async {
        await repository.getStringList('key');
      }, throwsStateError);
      expect(() async {
        await repository.getEnum<DummyEnum1>('key', DummyEnum1.values);
      }, throwsStateError);

      expect(() async {
        await repository.setBool(key: 'key', value: true);
      }, throwsStateError);
      expect(() async {
        await repository.setInt(key: 'key', value: 42);
      }, throwsStateError);
      expect(() async {
        await repository.setDouble(key: 'key', value: 13.37);
      }, throwsStateError);
      expect(() async {
        await repository.setString(key: 'key', value: 'value');
      }, throwsStateError);
      expect(() async {
        await repository.setStringList(key: 'key', value: <String>[]);
      }, throwsStateError);
      expect(() async {
        await repository.setEnum(key: 'key', value: DummyEnum1.item1);
      }, throwsStateError);
    });

    /// Ensures that null is returned for keys that have not been stored before
    test('read missing values', () async {
      // Create and initialize the repository instance, mocking the shared_preferences store with an
      // empty in-memory one (because all requested keys shall be missing).
      SharedPreferences.setMockInitialValues(<String, Object>{});
      SharedPreferencesRepository repository = SharedPreferencesRepository();
      await repository.initialize();

      expect(await repository.getBool('bool_key'), equals(null));
      expect(await repository.getInt('int_key'), equals(null));
      expect(await repository.getDouble('double_key'), equals(null));
      expect(await repository.getString('string_key'), equals(null));
      expect(await repository.getStringList('stringlist_key'), equals(null));
      expect(await repository.getEnum<DummyEnum1>('enum_key', DummyEnum1.values), equals(null));
    });

    /// Ensures that values can be stored and retrieved again
    test('store-read roundtrip', () async {
      // Create and initialize the repository instance, mocking the shared_preferences Flutter
      // plugin.
      SharedPreferences.setMockInitialValues(<String, Object>{});
      SharedPreferencesRepository repository = SharedPreferencesRepository();
      await repository.initialize();

      await repository.setBool(key: 'bool_key', value: true);
      expect(await repository.getBool('bool_key'), equals(true));

      await repository.setInt(key: 'int_key', value: 1337);
      expect(await repository.getInt('int_key'), equals(1337));

      await repository.setDouble(key: 'double_key', value: 47.11);
      expect(await repository.getDouble('double_key'), equals(47.11));

      await repository.setString(key: 'string_key', value: 'str');
      expect(await repository.getString('string_key'), equals('str'));

      await repository.setStringList(key: 'stringlist_key', value: <String>['a', 'b']);
      expect(await repository.getStringList('stringlist_key'), equals(<String>['a', 'b']));

      await repository.setEnum(key: 'enum_key', value: DummyEnum1.item2);
      expect(
        await repository.getEnum<DummyEnum1>('enum_key', DummyEnum1.values),
        equals(DummyEnum1.item2),
      );
    });

    /// Ensures that querying an existing key with the wrong value type throws a TypeError, except
    /// for enum values that cannot be mapped to the requested enum (return null in that case).
    test('type mismatch', () async {
      // Create and initialize the repository instance, mocking the shared_preferences Flutter
      // plugin.
      SharedPreferences.setMockInitialValues(<String, Object>{
        'bool_type': false,
        'int_type': 12345,
        'double_type': 3.1415,
        'string_type': 'something',
        'stringlist_type': <String>['aaa', 'bbb'],
        'enum_type': DummyEnum1.item2,
      });
      SharedPreferencesRepository repository = SharedPreferencesRepository();
      await repository.initialize();

      expect(() async {
        return repository.getBool('string_key');
      }, throwsA(isA<TypeError>()));
      expect(() async {
        return repository.getInt('bool_key');
      }, throwsA(isA<TypeError>()));
      expect(() async {
        return repository.getDouble('int_key');
      }, throwsA(isA<TypeError>()));
      expect(() async {
        return repository.getString('double_key');
      }, throwsA(isA<TypeError>()));
      expect(() async {
        return repository.getStringList('string_key');
      }, throwsA(isA<TypeError>()));
      expect(() async {
        return repository.getEnum<DummyEnum1>('bool_key', DummyEnum1.values);
      }, throwsA(isA<TypeError>()));

      // Special case: Unmappable enum value
      expect(await repository.getEnum<DummyEnum2>('enum_key', DummyEnum2.values), equals(null));
    });
  });
}
