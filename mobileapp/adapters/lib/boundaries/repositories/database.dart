///
/// Definition of the boundary between storage adapters (`adapters` ring) and a concrete repository
/// implementation (`infrastructure` ring).
///
library;

/// Boundary interface to a relational database.
///
/// A relational database is a repository organizing data in "entities" (tables) and "relations".
/// This interface provides generic access to a relational (e.g. SQL) database. Each implementation
/// encapsulates details like the used database engine or the used driver library. However, the
/// repository interface is schema-agnostic, which means that all information about the actual
/// structure (including information like table or column names) belong to the `adapters` ring.
///
/// The database can be either `connected` or `disconnected`. Most of its methods only work after
/// [connect()]ing to a database.
///
/// All database operations work synchronously.
abstract interface class RelationalDatabaseBoundary {
  /// Connects to the database specified by the [connectionString].
  void connect(String connectionString);

  /// Executes a query on a certain database table and returns the result set.
  ///
  /// The name of the table and the names of all columns to request must be specified by [table] and
  /// [columns]. The result rows are sorted by the column whose name is specified by [orderBy].
  /// [whereClause] allows to filter the result set, it is a regular SQL WHERE clause (without the
  /// WHERE keyword). [whereParameters] must be provided if the [whereClause] references query
  /// parameters ('?') to be bound later. Their count and order must correspond to the [whereClause].
  Future<ResultRows> queryTable(
    String table,
    List<String> columns, {
    String? whereClause,
    List<Object?> whereParameters = const <Object?>[],
    String? orderBy,
  });

  /// Executes a query on a (left) join between [leftTable] and [rightTable] and returns the result
  /// set.
  ///
  /// The join must be specified by [joinCondition] using a regular SQL condition clause (without
  /// the ON keyword). The names of all columns to request must be specified by [columns]. The
  /// result rows are grouped by the column whose names are specified with [groupBy] and ordered by
  /// the column name specified by [orderBy]. [whereClause] allows to filter the result set, it is a
  /// regular SQL WHERE clause (without the WHERE keyword). [whereParameters] must be provided if
  /// the [whereClause] references query parameters ('?') to be bound later. Their count and order
  /// must correspond to the [whereClause].
  Future<ResultRows> queryJoin(
    String leftTable,
    String rightTable,
    String joinCondition,
    List<String> columns, {
    String? whereClause,
    List<Object?> whereParameters = const <Object?>[],
    List<String>? groupBy,
    String? orderBy,
  });
}

/// A single row of a query result set.
class ResultRow {
  /// Raw result data row coming from the database.
  final Map<String, Object?> _resultData;

  /// Returns the value of the requested integer column [columnName].
  ///
  /// If the requested column doesn't exist in the result row or is of a different type, an error is
  /// thrown (because this is usually a programming error).
  int? getIntValue(String columnName) {
    return _resultData[columnName] as int?;
  }

  /// Returns the value of the requested floating-point column [columnName].
  ///
  /// If the requested column doesn't exist in the result row or is of a different type, an error is
  /// thrown (because this is usually a programming error).
  double? getDoubleValue(String columnName) {
    return _resultData[columnName] as double?;
  }

  /// Returns the value of the requested string column [columnName].
  ///
  /// If the requested column doesn't exist in the result row or is of a different type, an error is
  /// thrown (because this is usually a programming error).
  String? getStringValue(String columnName) {
    return _resultData[columnName] as String?;
  }

  /// Returns the value of the requested boolean column [columnName].
  ///
  /// If the requested column doesn't exist in the result row or is of a different type, an error is
  /// thrown (because this is usually a programming error).
  bool? getBoolValue(String columnName) {
    return _resultData[columnName] as bool?;
  }

  /// Initializes a new result row from raw data.
  ResultRow(this._resultData);
}

/// The result set returned by a table query.
typedef ResultRows = List<ResultRow>;
