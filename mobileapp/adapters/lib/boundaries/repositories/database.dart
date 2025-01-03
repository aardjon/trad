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
  ///
  /// If [readOnly] is set to true, the database is opened for reading only which allows some
  /// optimization (especially for concurrent access). However, trying to update any data will lead
  /// to an exception then.
  void connect(String connectionString, {bool readOnly = false});

  /// Closes the current database connection, if any.
  ///
  /// If no database is connected, this method does nothing.
  void disconnect();

  /// Returns true if the repository is currently connected to a database, otherwise false.
  bool isConnected();

  /// Executes the provided query and returns the result set.
  ///
  /// If the provided query is in any way invalid, an exception is raised. It the query doesn't
  /// return any results, the returned result row list is empty.
  Future<ResultRows> executeQuery(Query query);
}

/// Defines all properties and parameters of a query that can be run on the database.
///
/// To create a simple table query, use [Query.table()]. For joining several tables, use
/// [Query.join()].
///
/// This class is merely for transporting and representing queries, it doesn't do much validation.
/// It can be executed by handing it to [RelationalDatabaseBoundary.executeQuery()], which will
/// cause an error if the query is in any way invalid (e.g. non-existent column names, parameter
/// count mismatch etc).
class Query {
  /// Table names to query.
  final List<String> _tableNames;

  /// Join conditions (for joins only). This list is one item shorter than [_tableNames].
  final List<String>? _joinConditions;

  /// Columns to retrieve.
  final List<String> _columnNames;

  /// The WHERE condition.
  String? _whereCondition;

  /// WHERE parameters.
  List<Object?> _whereParameters = const <Object?>[];

  /// Names of the tables to query.
  List<String> get tableNames => _tableNames;

  /// The SQL JOIN conditions (without the ON keywords) in case [tableNames] contains more than one.
  ///
  /// The length of the returned list is always the number of [tableNames] minus one.
  List<String>? get joinConditions => _joinConditions;

  /// The names of the columns to retrieve.
  List<String> get columNames => _columnNames;

  /// The SQL WHERE condition to filter by (without the WHERE keyword).
  String? get whereCondition => _whereCondition;

  /// Parameter values referenced by [whereCondition].
  List<Object?> get whereParameters => _whereParameters;

  /// Specifies the names of the columns the result rows are grouped by.
  List<String> groupByColumns = <String>[];

  /// Specifies the names of the columns the result rows are ordered by.
  List<String> orderByColumns = <String>[];

  /// Defines a query on a single database table.
  ///
  /// The name of the table and the names of all columns to request must be specified by [tableName]
  /// and [_columnNames]. The column names specified here are used to retrieve the resulting values
  /// from [ResultRow] objects after the query has run.
  Query.table(String tableName, this._columnNames)
      : _tableNames = <String>[tableName],
        _joinConditions = null,
        assert(_columnNames.isNotEmpty, 'At least one column to retrieve must be defined');

  /// Defines a query on a (left) join between the specified tables.
  ///
  /// The tables specified by [_tableNames] are joined using the given [joinConditions], which is a
  /// list of regular SQL condition clauses without the ON keywords. Its length must be the number
  /// of provided [_tableNames] minus one.
  ///
  /// The names of all columns to request must be specified by [_columnNames]. The column names
  /// specified here are used to retrieve the resulting values from [ResultRow] objects after the
  /// query has run.
  Query.join(this._tableNames, List<String> joinConditions, this._columnNames)
      : assert(_tableNames.length > 1, 'Joining requires at least two table names.'),
        assert(
          joinConditions.length == _tableNames.length - 1,
          "Joining requires 'table count - 1' join conditions.",
        ),
        _joinConditions = joinConditions,
        assert(_columnNames.isNotEmpty, 'At least one column to retrieve must be defined');

  /// Defines a condition to filter the result set for.
  ///
  /// [whereCondition] is a regular SQL WHERE clause without the WHERE keyword. All non-static
  /// parameter values should be provided in the [whereParameters] list and only referenced by '?'
  /// within [whereCondition]. This avoids SQL injection errors. Of course, the number of given
  /// parameters must match the number of references, otherwise the query will fail upon execution.
  void setWhereCondition(String whereCondition, List<Object?> whereParameters) {
    _whereCondition = whereCondition;
    _whereParameters = whereParameters;
  }
}

/// A single row of a query result set.
///
/// All cell values are accessed based on their column name. These names are the same as configured
/// for retrieval by [Query.tableNames].
class ResultRow {
  /// Raw result data row coming from the database.
  final Map<String, Object?> _resultData;

  /// Returns the value of the requested integer column [columnName].
  ///
  /// If the requested column doesn't exist in the result row or is of a different type, an
  /// [ArgumentError] is thrown (because this is usually a programming error).
  int getIntValue(String columnName) {
    return _getValue(columnName)! as int;
  }

  /// Returns the value of the requested nullable integer column [columnName].
  ///
  /// If the requested column doesn't exist in the result row or is of a different type, an
  /// [ArgumentError] is thrown (because this is usually a programming error).
  int? getOptIntValue(String columnName) {
    return _getValue(columnName) as int?;
  }

  /// Returns the value of the requested floating-point column [columnName].
  ///
  /// If the requested column doesn't exist in the result row or is of a different type, an
  /// [ArgumentError] is thrown (because this is usually a programming error).
  double getDoubleValue(String columnName) {
    return _getValue(columnName)! as double;
  }

  /// Returns the value of the requested nullable floating-point column [columnName].
  ///
  /// If the requested column doesn't exist in the result row or is of a different type, an
  /// [ArgumentError] is thrown (because this is usually a programming error).
  double? getOptDoubleValue(String columnName) {
    return _getValue(columnName) as double?;
  }

  /// Returns the value of the requested string column [columnName].
  ///
  /// If the requested column doesn't exist in the result row or is of a different type, an
  /// [ArgumentError] is thrown (because this is usually a programming error).
  String getStringValue(String columnName) {
    return _getValue(columnName)! as String;
  }

  /// Returns the value of the requested nullable string column [columnName].
  ///
  /// If the requested column doesn't exist in the result row or is of a different type, an
  /// [ArgumentError] is thrown (because this is usually a programming error).
  String? getOptStringValue(String columnName) {
    return _getValue(columnName) as String?;
  }

  /// Returns the value of the requested boolean column [columnName].
  ///
  /// If the requested column doesn't exist in the result row or is of a different type, an
  /// [ArgumentError] is thrown (because this is usually a programming error).
  bool getBoolValue(String columnName) {
    return _getValue(columnName)! as bool;
  }

  /// Returns the value of the requested nullable boolean column [columnName].
  ///
  /// If the requested column doesn't exist in the result row or is of a different type, an
  /// [ArgumentError] is thrown (because this is usually a programming error).
  bool? getOptBoolValue(String columnName) {
    return _getValue(columnName) as bool?;
  }

  /// Initializes a new result row from raw data.
  ResultRow(this._resultData);

  /// Returns the value of the given [columnName] if the column exists in the result set.
  ///
  /// The value may still be null (for NULLABLE columns). If the result set doesn't contain the
  /// requested column at all, an [ArgumentError] is thrown. This usually means that the column has
  /// not been selected when defining the query.
  Object? _getValue(String columnName) {
    if (_resultData.containsKey(columnName)) {
      return _resultData[columnName];
    }
    throw ArgumentError(
      'Column $columnName is not available in the result set, did you forget to select it?',
      'columnName',
    );
  }
}

/// The result set returned by a table query.
typedef ResultRows = List<ResultRow>;
