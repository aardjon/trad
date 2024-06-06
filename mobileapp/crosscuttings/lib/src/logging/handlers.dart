///
/// Implementations of the different log handlers.
///
/// This library is not part of the public logging API and is thus meant to be used within
/// `trad.crossuttings.logging` only.
///
library;

import 'dart:convert';
import 'dart:io';

import 'package:logging/logging.dart' as loglib;

/// Base class for handling log records appropriately.
///
/// This uses the `template method` design pattern to create the message string but delegating the
/// actual message writing to specialized derived classes (which must implement the
/// [_writeMessage()] method). Each derived class defines a single log destination.
abstract class LogHandler {
  /// Formatter which creates the final message string from a [loglib.LogRecord].
  final _LogFormatter _formatter = _LogFormatter();

  /// Processes a single log record (i.e. a single message).
  ///
  /// This is the template method which is called once for every [record] to log. It is registered
  /// as listener to the underlying logging library.
  void handleRecord(loglib.LogRecord record) {
    String message = _formatter.format(record);
    _writeMessage(message);
  }

  /// Abstract method that writes the given [message] to the concrete log destination.
  void _writeMessage(String message);
}

/// A log handler printing all messages to stdout.
class ConsoleLogHandler extends LogHandler {
  @override
  void _writeMessage(String message) {
    // We usually want to use the logging framework instead of print(). However, as this *is* the
    // logging framework implementation that prints a logged message to stdout, this is literally
    // the only place where using print() is accepted. That's why we ignore the linter error here.
    // ignore: avoid_print
    print(message);
  }
}

/// A log handler writing all messages into a single text file.
///
/// All messages are written synchronously, each time opening and closing the destination file.
/// While this is can slow down the application, it has the advantage of writing as soon as possible
/// and provides a high probability for having helpful log in case of an application crash.
class FileLogHandler extends LogHandler {
  /// The (text) file to write all log messages into.
  final File _logFile;

  /// Constructor for directly initializing all members.
  FileLogHandler(String logFilePath) : _logFile = File(logFilePath);

  @override
  void _writeMessage(String message) {
    _logFile.writeAsStringSync(
      message + Platform.lineTerminator,
      mode: FileMode.append,
      encoding: utf8,
      flush: true,
    );
  }
}

/// A log handler that stores all messages in memory.
///
/// Useful to not lose messages when no other destination is available (yet). Use with caution,
/// though.
class MemoryLogHandler extends LogHandler {
  /// Reference to the list to write all log messages into.
  final List<String> _loggedMessages;

  /// Constructor for directly initializing all members.
  ///
  /// All log messages will be appended to the provided list.
  MemoryLogHandler(this._loggedMessages);

  @override
  void _writeMessage(String message) {
    _loggedMessages.add(message);
  }
}

/// Special handler (null object) that absorbs all log records but never logs anything.
///
/// Used as default handler and in case logging shall be disabled completely.
class BlackholeLogHandler extends LogHandler {
  @override
  void _writeMessage(String message) {}
}

/// Formatter that creates string representations of log records.
///
/// This class is responsible for generating the actual, formatted string messages that will be
/// written. Even though there is only this one implementation (yet), it's a class already to make
/// future extensions easier.
class _LogFormatter {
  /// Create the final string representation for the given log {record].
  String format(loglib.LogRecord record) {
    final String levelName = record.level.name.toUpperCase();
    return '[${record.time}][$levelName][${record.loggerName}] ${record.message}';
  }
}
