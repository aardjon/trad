///
/// SQLite3 implementation of the [RelationalDatabaseBoundary] repository.
///
library;

import 'package:sqlite3/sqlite3.dart';

import 'package:adapters/boundaries/repositories/database.dart';
import 'package:crosscuttings/logging/logger.dart';

/// Logger to be used in this library file.
final Logger _logger = Logger('trad.infrastructure_vanilla.repositories.sqlite3');

/// SQLite3 based implementation of the relational database.
///
/// This implementation encapsulates the `sqlite3` package and therefore all its details. When
/// [connect()]ing to a SQLite database, the connectionString is simply the full path to the SQLite
/// database file to open.
class Sqlite3Database implements RelationalDatabaseBoundary {
  /// Interface to the sqlite3 library.
  ///
  /// Having this as a separate member allows to replace the real library with a different or mocked
  /// one, e.g. for unit testing. Never use `sqlite3` directly but only this member.
  final Sqlite3 _extLibApi;

  /// Handle to the currently opened database, or `null` if no database has been opened.
  Database? _dbHandle;

  /// Constructor for injecting an alternative sqlite3 library.
  ///
  /// For easier unit testing, a mocked sqlite3 library can be injected by providing it as
  /// [extLibApi]. In normal/productive cases always use the default parameter value.
  Sqlite3Database({Sqlite3? extLibApi}) : _extLibApi = extLibApi ?? sqlite3;

  @override
  void connect(String connectionString, {bool readOnly = false}) {
    _dbHandle = _extLibApi.open(
      connectionString,
      mode: readOnly ? OpenMode.readOnly : OpenMode.readWriteCreate,
    );
  }

  @override
  Future<ResultRows> queryJoin(
    String leftTable,
    String rightTable,
    String joinCondition,
    List<String> columns, {
    String? whereClause,
    List<Object?> whereParameters = const <Object?>[],
    List<String>? groupBy,
    String? orderBy,
  }) async {
    if (_dbHandle == null) {
      throw StateError('Please connect() to a database before querying it.');
    }
    // TODO(aardjon): Check whereClause and whereParameters validity
    ResultRows resultRows = <ResultRow>[];

    /// To be able to reference the columns in the result set by the same name as they are
    /// requested, we always use the AS keyword. But only if the client didn't specify one by
    /// itself, of course.
    List<String> normalizedColumnNames = <String>[];
    for (final String colName in columns) {
      if (!colName.contains(' AS ')) {
        normalizedColumnNames.add("$colName AS '$colName'");
      } else {
        normalizedColumnNames.add(colName);
      }
    }
    String sqlStatement = "SELECT ${normalizedColumnNames.join(', ')} "
        "FROM '$leftTable' "
        "LEFT JOIN '$rightTable' ON $joinCondition";
    if (whereClause != null) {
      sqlStatement += ' WHERE $whereClause';
    }
    if (groupBy != null) {
      sqlStatement += " GROUP BY ${groupBy.join(', ')}";
    }
    if (orderBy != null) {
      sqlStatement += ' ORDER BY $orderBy';
    }

    _logger.debug('Executing SQL statement: $sqlStatement');
    ResultSet resultSet = _dbHandle!.select(sqlStatement, whereParameters);

    for (final Row row in resultSet) {
      resultRows.add(ResultRow(row));
    }
    return resultRows;
  }

  @override
  Future<ResultRows> queryTable(
    String table,
    List<String> columns, {
    String? whereClause,
    List<Object?> whereParameters = const <Object?>[],
    String? orderBy,
  }) async {
    if (_dbHandle == null) {
      throw StateError('Please connect() to a database before querying it.');
    }
    ResultRows resultRows = <ResultRow>[];

    /// To be able to reference the columns in the result set by the same name as they are
    /// requested, we always use the AS keyword. But only if the client didn't specify one by
    /// itself, of course.
    List<String> normalizedColumnNames = <String>[];
    for (final String colName in columns) {
      if (!colName.contains(' AS ')) {
        normalizedColumnNames.add("$colName AS '$colName'");
      } else {
        normalizedColumnNames.add(colName);
      }
    }

    String sqlStatement = "SELECT ${normalizedColumnNames.join(', ')} FROM '$table' ";
    if (whereClause != null) {
      sqlStatement += 'WHERE $whereClause ';
    }
    if (orderBy != null) {
      sqlStatement += 'ORDER BY $orderBy';
    }

    _logger.debug('Executing SQL statement: $sqlStatement');
    ResultSet resultSet = _dbHandle!.select(sqlStatement, whereParameters);

    for (final Row row in resultSet) {
      resultRows.add(ResultRow(row));
    }
    return resultRows;
  }
}
