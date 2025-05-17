///
/// Wrappers for the `logging` package used internally.
///
/// This library delegates API requests to the library, mapping/converting data structures as
/// necessary. It is not part of the public logging API and is thus meant to be used within
/// `trad.crossuttings.logging` only.
///
library;

import 'package:logging/logging.dart' as loglib;

import '../../logging/config.dart';
import './handlers.dart';

/// Adapter connecting the package interface (Logger) to the actual implementation (the `logging`
/// library).
///
/// This class maps package log channels to corresponding logging lib channels. This mapping must be
/// the same as [LogConfigWrapper] does.
class LoggerWrapper {
  /// The real (`logging`) logger this instance delegates to
  final loglib.Logger _realLogger;

  /// Creates a new Logger instance for the provided channel name.
  LoggerWrapper(String channelName) : _realLogger = loglib.Logger(channelName);

  /// Logs a message with level `LogLevel.fatal` on this logger.
  void fatal(Object? message, [Object? error, StackTrace? stackTrace]) {
    _realLogger.shout(message, error, stackTrace);
  }

  /// Logs a message with level `LogLevel.error` on this logger.
  void error(Object? message, [Object? error, StackTrace? stackTrace]) {
    _realLogger.severe(message, error, stackTrace);
  }

  /// Logs a message with level `LogLevel.warning` on this logger.
  void warning(Object? message, [Object? error, StackTrace? stackTrace]) {
    _realLogger.warning(message, error, stackTrace);
  }

  /// Logs a message with level `LogLevel.info` on this logger.
  void info(Object? message, [Object? error, StackTrace? stackTrace]) {
    _realLogger.info(message, error, stackTrace);
  }

  /// Logs a message with level `LogLevel.debug` on this logger.
  void debug(Object? message, [Object? error, StackTrace? stackTrace]) {
    _realLogger.fine(message, error, stackTrace);
  }

  /// Logs a message with level `LogLevel.trace` on this logger.
  void trace(Object? message, [Object? error, StackTrace? stackTrace]) {
    _realLogger.finest(message, error, stackTrace);
  }
}

/// Adapter connecting the package interface to the actual implementation.
///
/// This class maps package log channels to corresponding logging lib channels. This mapping must be
/// the same as [LoggerWrapper] does.
class LogConfigWrapper {
  /// Set the global log [destination] to the provided one.
  ///
  /// Any previously set destination is replaced, all future messages are sent the new destination.
  void updateDestination(LogDestination destination) {
    LogHandler logHandler = _createLogHandler(destination);
    loglib.Logger rootLogger = loglib.Logger.root;
    rootLogger.clearListeners();
    rootLogger.onRecord.listen((loglib.LogRecord libRecord) {
      logHandler.handleRecord(libRecord);
    });
  }

  /// Set the global log [level] to the requested one.
  ///
  /// This change is applied to all future messages.
  void updateGlobalLevel(LogLevel level) {
    loglib.Logger.root.level = _mapToLibLevel(level);
  }

  /// Factory for creating a [LogHandler] that corresponds to the given [destination].
  ///
  /// Throws an [ArgumentError] in case the destination cannot be mapped (did you forget to
  /// implement a [LogHandler] for a newly created [LogDestination]?).
  LogHandler _createLogHandler(LogDestination destination) {
    if (destination is FileLogDestination) {
      return FileLogHandler(destination.logFilePath);
    } else if (destination is ConsoleLogDestination) {
      return ConsoleLogHandler();
    } else if (destination is BlackholeLogDestination) {
      return BlackholeLogHandler();
    } else if (destination is MemoryLogDestination) {
      return MemoryLogHandler(destination.loggedMessages);
    }
    throw ArgumentError(
      'Unable to create log handler for unexpected destination of type '
      "'${destination.runtimeType}'",
    );
  }

  /// Returns the internal (logging lib) value representing the requested API log level.
  loglib.Level _mapToLibLevel(LogLevel level) {
    switch (level) {
      case LogLevel.off:
        return loglib.Level.OFF;
      case LogLevel.fatal:
        return loglib.Level.SHOUT;
      case LogLevel.error:
        return loglib.Level.SEVERE;
      case LogLevel.warning:
        return loglib.Level.WARNING;
      case LogLevel.info:
        return loglib.Level.INFO;
      case LogLevel.debug:
        return loglib.Level.FINE;
      case LogLevel.trace:
        return loglib.Level.FINEST;
      case LogLevel.all:
        return loglib.Level.ALL;
    }
  }
}
