///
/// Unit tests for the infrastructure_vanilla.repositories.sqlite3 component.
///
library;

import 'package:mocktail/mocktail.dart';
import 'package:sqlite3/sqlite3.dart';
import 'package:test/test.dart';

import 'package:adapters/boundaries/repositories/database.dart';
import 'package:infrastructure_vanilla/repositories/sqlite3.dart';

class _SqliteApiMock extends Mock implements Sqlite3 {}

class _DatabaseMock extends Mock implements Database {}

/// Parameters for a single `executeQuery` test case:
/// $1: Factory creating the Query object for the test case
/// $2: Complete SQL statement expected to be executed
typedef _QueryTableTestParameters = (Query Function(), String);

/// Unit tests for the infrastructure_vanilla.sqlite3.Sqlite3Database class.
void main() {
  setUpAll(() {
    // Register a default OpenMode object which is used by mocktails `any` matcher
    registerFallbackValue(OpenMode.readWrite);
  });

  /// Ensures that all query method() raise a exception if called when the database has not been
  /// opened before.
  test('infrastructure_vanilla.sqlite3.Sqlite3Database.testDisconnectedState', () {
    Sqlite3Database database = Sqlite3Database();

    expect(() async {
      await database.executeQuery(Query.table('dummyTable', <String>['dummy']));
    }, throwsStateError);
  });

  String dummySqliteFilePath = '/some/file/path.sqlite';

  /// Unit test for the connect() method.
  ///
  /// Ensures that the database is opened with the correct mode as requested by the readOnly flag.
  group('infrastructure_vanilla.sqlite3.Sqlite3Database.testConnect', () {
    /// List of test parameters for infrastructure_vanilla.sqlite3.Sqlite3Database.testConnect.
    ///
    /// Each list item is record of [bool readOnly, OpenMode expectedOpenMode] with:
    ///  - `readOnly` being the equally named parameter of connect()
    ///  - `expectedOpenMode` being the resulting OpenMode expected on Sqlite3 side
    List<(bool, OpenMode)> testParameters = <(bool, OpenMode)>[
      (true, OpenMode.readOnly),
      (false, OpenMode.readWriteCreate),
    ];

    for (final (bool, OpenMode) singleRunParams in testParameters) {
      test('readOnly=${singleRunParams.$1}', () {
        final _SqliteApiMock sqliteMock = _SqliteApiMock();
        final _DatabaseMock dbMock = _DatabaseMock();
        when(() => sqliteMock.open(any(), mode: any(named: 'mode'))).thenReturn(dbMock);

        Sqlite3Database database = Sqlite3Database(extLibApi: sqliteMock);
        database.connect(dummySqliteFilePath, readOnly: singleRunParams.$1);

        verify(() => sqliteMock.open(dummySqliteFilePath, mode: singleRunParams.$2)).called(1);
      });
    }
  });

  /// Unit test for the disconnect() method.
  ///
  /// Ensures that:
  ///  - the database is really closed again
  ///  - calling disconnect() on a closed database doesn't do any harm
  group('infrastructure_vanilla.sqlite3.Sqlite3Database.testDisconnect', () {
    // The parameter [dbIsConnected] defines whether the database should be connect()ed before
    // calling disconnect().
    for (final bool dbIsConnected in <bool>[true, false]) {
      test('connected=$dbIsConnected', () {
        final _SqliteApiMock sqliteMock = _SqliteApiMock();
        final _DatabaseMock dbMock = _DatabaseMock();
        when(() => sqliteMock.open(any(), mode: any(named: 'mode'))).thenReturn(dbMock);

        Sqlite3Database database = Sqlite3Database(extLibApi: sqliteMock);
        if (dbIsConnected) {
          database.connect('/some/random/file.sqlite');
        }

        // The disconnect() call must not throw
        expect(database.disconnect, returnsNormally);

        if (dbIsConnected) {
          verify(dbMock.dispose).called(1);
        } else {
          verifyNever(dbMock.dispose);
        }
      });
    }
  });

  /// Unit test for the executeQuery() method.
  ///
  /// Ensures that the expected values are given to the sqlite3 library for certain Query instances:
  ///  - the SQL statement string is as expected
  ///  - the WHERE parameters (if any) are as forwarded as they are
  group('infrastructure_vanilla.sqlite3.Sqlite3Database.testExecuteQuery', () {
    List<_QueryTableTestParameters> testParameters = <_QueryTableTestParameters>[
      // Simple SELECT statement with multiple rows
      (
        () => Query.table('table', <String>['id', 'table.name']),
        "SELECT id AS 'id', table.name AS 'table.name' FROM 'table'",
      ),
      // Leave explicit AS columns as they are
      (() => Query.table('table', <String>['name AS blubb']), "SELECT name AS blubb FROM 'table'"),
      // Joins are also supported
      (
        () => Query.join(
          <String>['table1', 'table2'],
          <String>['table1.id = table2.tab1_id'],
          <String>['table1.id'],
        ),
        "SELECT table1.id AS 'table1.id' FROM 'table1' LEFT JOIN 'table2' ON table1.id = table2.tab1_id",
      ),
      // Ensure WHERE clauses work
      (
        () =>
            Query.table('table', <String>['name', 'city'])
              ..setWhereCondition('city = ?', <Object?>['Springfield']),
        "SELECT name AS 'name', city AS 'city' FROM 'table' WHERE city = ?",
      ),
      // Ensure ORDER BY works
      (
        () => Query.table('table', <String>['name'])..orderByColumns = <String>['name'],
        "SELECT name AS 'name' FROM 'table' ORDER BY name",
      ),
      // Ensure GROUP BY works
      (
        () => Query.table('table', <String>['name'])..groupByColumns = <String>['name', 'city'],
        "SELECT name AS 'name' FROM 'table' GROUP BY name, city",
      ),
      // Ensure LIMIT works
      (
        () => Query.table('table', <String>['name'])..limit = 3,
        "SELECT name AS 'name' FROM 'table' LIMIT 3",
      ),
    ];

    for (final _QueryTableTestParameters singleRunParams in testParameters) {
      Query query = singleRunParams.$1();
      String expectedSqlStatement = singleRunParams.$2;

      test(expectedSqlStatement, () async {
        final _SqliteApiMock sqliteMock = _SqliteApiMock();
        final _DatabaseMock sqliteDbMock = _DatabaseMock();
        when(() => sqliteMock.open(any(), mode: any(named: 'mode'))).thenReturn(sqliteDbMock);
        when(
          () => sqliteDbMock.select(any(), any()),
        ).thenReturn(ResultSet(<String>[], <String>[], <List<Object?>>[]));
        Sqlite3Database database = Sqlite3Database(extLibApi: sqliteMock);
        database.connect(dummySqliteFilePath);

        await database.executeQuery(query);

        verify(() => sqliteDbMock.select(expectedSqlStatement, query.whereParameters)).called(1);
      });
    }
  });
}
