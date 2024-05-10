///
/// Implementations of the different log handlers.
/// This library is not part of the public logging API and is thus meant to be used within
/// `trad.crossuttings.logging` only.
///
library;

import 'dart:io';
import 'dart:convert';

import 'package:logging/logging.dart' as loglib;

/// Base class for handling log records appropriately.
/// This uses the `template method` design pattern to create the message string but delegating
/// the actual message writing to specialized derived classes (which must implement the
/// [_writeMessage()] method).
abstract class LogHandler {
  final _LogFormatter _formatter = _LogFormatter();

  void handleRecord(loglib.LogRecord record) {
    String message = _formatter.format(record);
    _writeMessage(message);
  }

  void _writeMessage(String message);
}

/// A log handler writing all messages into a single file.
class FileLogHandler extends LogHandler {
  final File _logFile;

  FileLogHandler(String logFilePath) : _logFile = File(logFilePath);

  @override
  void _writeMessage(String message) {
    _logFile.writeAsStringSync(message + Platform.lineTerminator,
        mode: FileMode.append, encoding: utf8, flush: true);
  }
}

/// Special handler (null object) that absorbs all log records but never logs anything.
/// Used as default handler and in case logging shall be disabled completely.
class BlackholeLogHandler extends LogHandler {
  @override
  void _writeMessage(String message) {}
}

class _LogFormatter {
  String format(loglib.LogRecord record) {
    final String levelName = record.level.name.toUpperCase();
    return '[${record.time}][$levelName][${record.loggerName}] ${record.message}';
  }
}
