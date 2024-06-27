///
/// Logging library that can be used by all parts of the trad application.
///
/// Together with `trad.crosscuttings.logging.entities`, this library is the public logging API.
///
library;

import '../src/logging/wrapper.dart';
import 'config.dart';

export 'config.dart';

/// Logger for writing messages to a certain channel.
///
/// Each instance of this class writes to the channel identified by the name given on creation. It's
/// okay to have several [Logger] instances writing to the same channel. A good practise is to
/// create one [Logger] per source file.
///
/// Usage example:
/// ```dart
/// Logger logger = Logger('trad.core.example');
/// logger.info('Created the first logger');
/// ```
///
/// Messages are only processed if they are of the same (or a higher) importance as the configured
/// one, please refer to the [LogLevel] class for a description of the available levels. See the
/// [LogConfiguration] class for information about configuring the log output.
class Logger {
  /// The library wrapper this instance delegates to.
  final LoggerWrapper _wrapper;

  /// Creates a new [Logger] which sends its messages to the channel with the provided
  /// [channelName].
  ///
  /// The [channelName] must start with `trad`  and reflect the source/architectural position of
  /// the module the `Logger` instance is created in, using single dots as delimeters (e.g.
  /// `trad.core.usecases.journal`). This makes it easy to filter for messages from a certain system
  /// part later on.
  Logger(String channelName) : _wrapper = LoggerWrapper(channelName);

  /// Logs a [message] on the `LogLevel.fatal` level.
  void fatal(Object? message, [Object? error, StackTrace? stackTrace]) {
    _wrapper.fatal(message, error, stackTrace);
  }

  /// Logs a [message] on the `LogLevel.error` level.
  void error(Object? message, [Object? error, StackTrace? stackTrace]) {
    _wrapper.error(message, error, stackTrace);
  }

  /// Logs a [message] on the `LogLevel.warning` level.
  void warning(Object? message, [Object? error, StackTrace? stackTrace]) {
    _wrapper.warning(message, error, stackTrace);
  }

  /// Logs a [message] on the `LogLevel.info` level.
  void info(Object? message, [Object? error, StackTrace? stackTrace]) {
    _wrapper.info(message, error, stackTrace);
  }

  /// Logs a [message] on the `LogLevel.debug` level.
  void debug(Object? message, [Object? error, StackTrace? stackTrace]) {
    _wrapper.debug(message, error, stackTrace);
  }

  /// Logs a [message] on the `LogLevel.trace` level.
  void trace(Object? message, [Object? error, StackTrace? stackTrace]) {
    _wrapper.trace(message, error, stackTrace);
  }
}

/// Central configuration instance of the logging library.
///
/// This class is the entry point for configuring the log output. It is a singleton because there
/// is only one global log configuration which applies to all created [Logger]s.
class LogConfiguration {
  // The global singleton instance.
  static final LogConfiguration _singletonInstance = LogConfiguration._instantiate();

  /// The configured log level.
  LogLevel _globalLevel = LogLevel.info;

  // The configured log destination.
  LogDestination _destination = BlackholeLogDestination();

  /// The wrapper object this instance delegates to.
  final LogConfigWrapper _wrapper = LogConfigWrapper();

  /// Returns the global [LogConfiguration] instance.
  factory LogConfiguration() {
    return LogConfiguration._singletonInstance;
  }

  /// Private constructor for initially creating a [LogConfiguration] instance.
  LogConfiguration._instantiate();

  /// Returns the currently configured log level.
  LogLevel get globalLevel => _globalLevel;

  /// Changes the currently configured log level to [level].
  ///
  /// The change will be respected for all future messages from all [Logger]s.
  set globalLevel(LogLevel level) {
    _globalLevel = level;
    _wrapper.updateGlobalLevel(_globalLevel);
  }

  /// Returns the currently configured log destination.
  LogDestination get destination => _destination;

  /// Changes the currently configured log destination.
  ///
  /// The change will be respected for all future messages from all [Logger]s. Throws an
  /// `ArgumentError` if the provided [LogDestination] is unknown.
  set destination(LogDestination destination) {
    _destination = destination;
    _wrapper.updateDestination(_destination);
  }
}
