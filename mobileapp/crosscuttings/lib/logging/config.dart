///
/// Contains data types for configuring the logging.
/// This library is part of the public logging API, but it is not relevant for just writing log
/// messages but only for configuring the logging library.
///
library;

/// Represents the importance a log message has.
/// Messages of the [fatal] level are considered more important or "higher" than messages of the
/// [trace] level.
enum LogLevel {
  /// Special level to turn off *all* log messages, even the most critical ones. Use with
  /// caution.
  off,

  /// A critial error that may cause the program to stop running.
  fatal,

  /// Some function could not be performed because of a serious problem.
  error,

  /// Something unexpected happened or a problem might occur in the near future, but the
  /// software is still working as expected.
  warning,

  /// Information things thats are working as expected.
  info,

  /// Detailed information, typically only of interest to a developer trying to diagnose a
  /// problem.
  debug,

  /// Most verbose information that go even beyond the debug scope, e.g. for tracing single
  /// function calls.
  trace,

  /// Special level to enable really *all* log messages.
  all;
}

/// Base class for defining where logs shall finally go to.
/// A [LogDestination] configures the final sink all messages (from all [Logger]s) are finally
/// written into (e.g. a file or console). This is only about the configuration, it does not
/// actually handle any output.
abstract class LogDestination {}

/// A (noop) destination for absorbing all messages and never logging anything.
/// Can be used as default or to definitely disable all logging. However, to disable logging it
/// is usually better to set the log level to `LogLevel.off` because this will avoid some
/// overhead like message string creation and propagation and therefore improve performance.
class BlackholeLogDestination extends LogDestination {}

/// A destination for keeping all logged messaged in memory. They will be gone after the
/// application shutdown.
class MemoryLogDestination extends LogDestination {
  List<String> loggedMessages = [];
}

/// A destination for sending all messages to stdout.
class ConsoleLogDestination extends LogDestination {}

/// A destination for writing all messages to a single, endlessly growing file.
/// The file must be writable and is created if it does not exist yet.
class FileLogDestination extends LogDestination {
  /// Full path to the log file.
  String logFilePath;

  /// Creates a new instance for writing into the provided [logFilePath] file.
  FileLogDestination(this.logFilePath);
}
