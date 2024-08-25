///
/// Definition of the [SqlStmtFactory] class.
///
library;

import 'package:adapters/boundaries/repositories/database.dart';

/// A factory creating SQL statement strings from [Query] objects.
class SqlStmtFactory {
  /// Generates the SQL statement for the given [query].
  String generateSqlStatement(Query query) {
    StringBuffer sqlBuffer = StringBuffer();
    sqlBuffer.write(_generateSelectPart(query));
    sqlBuffer.write(_generateTableJoinPart(query));
    sqlBuffer.write(_generateWhereClause(query));
    sqlBuffer.write(_generateGroupByPart(query));
    sqlBuffer.write(_generateOrderByPart(query));
    return sqlBuffer.toString();
  }

  String _generateSelectPart(Query query) {
    final List<String> normalizedColumnNames = _normalizeColumnNames(query.columNames);
    return "SELECT ${normalizedColumnNames.join(', ')}";
  }

  /// Generates the FROM part of the SQL statement, including all JOIN...ON stuff (if any).
  String _generateTableJoinPart(Query query) {
    StringBuffer buffer = StringBuffer();
    buffer.write(" FROM '${query.tableNames[0]}'");
    for (int i = 1; i < query.tableNames.length; ++i) {
      buffer.write(" LEFT JOIN '${query.tableNames[i]}' ON ${query.joinConditions![i - 1]}");
    }
    return buffer.toString();
  }

  String _generateWhereClause(Query query) {
    return query.whereCondition != null ? ' WHERE ${query.whereCondition}' : '';
  }

  String _generateGroupByPart(Query query) {
    return query.groupByColumns.isNotEmpty ? " GROUP BY ${query.groupByColumns.join(', ')}" : '';
  }

  String _generateOrderByPart(Query query) {
    return query.orderByColumns.isNotEmpty ? " ORDER BY ${query.orderByColumns.join(', ')}" : '';
  }

  /// Returns a normalized copy of the column name list.
  ///
  /// To be able to reference the columns in the result set by the same name as they are
  /// requested, we always use the AS keyword. But only if the client didn't specify one by
  /// itself, of course.
  List<String> _normalizeColumnNames(List<String> columnNames) {
    List<String> normalizedColumnNames = <String>[];
    for (final String colName in columnNames) {
      if (!colName.contains(' AS ')) {
        normalizedColumnNames.add("$colName AS '$colName'");
      } else {
        normalizedColumnNames.add(colName);
      }
    }
    return normalizedColumnNames;
  }
}
