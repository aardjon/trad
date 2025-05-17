///
/// Unit tests for the crosscuttings.logging library.
///
library;

import 'dart:io';

import 'package:test/test.dart';

import 'package:crosscuttings/logging/logger.dart';

/// Example exception for testing the exception logging mechanism.
class _ExampleException implements Exception {
  static const String message = 'Exception Message';

  @override
  String toString() {
    return message;
  }
}

/// Example StackTrace for testing the stack trace logging mechanism.
class _ExampleStackTrace implements StackTrace {
  static const String message = 'StackTrace Message';

  @override
  String toString() {
    return message;
  }
}

/// Type of a concrete log function (i.e. a Logger method). Used for test case parametrization.
typedef _LogFunction = void Function(String message, Exception? error, StackTrace? stackTrace);

/// Unit tests for the crosscuttings.logging component.
void main() {
  /// Test cases for correct level propagation and filtering
  group('crosscuttings.logging.loglevels', () {
    setUp(() {
      // Configure logging to write to a file
      final LogConfiguration logConfig = LogConfiguration();
      logConfig.destination = MemoryLogDestination();
    });

    /// Ensure that all messages matching the log level configuration are be written to the log
    /// file. To achieve this, two messages are written to each level. The [level] parameter
    /// defines the level until which the messages must end up in the file. The
    /// [expectedMessageCount] defines the number of log messages that are expected to end up in
    /// the log file. If no messages are written, the file must not be created at all.
    List<(LogLevel, int)> testCaseParams = <(LogLevel, int)>[
      (LogLevel.all, 12),
      (LogLevel.trace, 12),
      (LogLevel.debug, 10),
      (LogLevel.info, 8),
      (LogLevel.warning, 6),
      (LogLevel.error, 4),
      (LogLevel.fatal, 2),
      (LogLevel.off, 0),
    ];
    for (final (LogLevel, int) testParams in testCaseParams) {
      LogLevel level = testParams.$1;
      int expectedMessageCount = testParams.$2;

      test(level, () {
        // Configure the log level
        final LogConfiguration logConfig = LogConfiguration();
        logConfig.globalLevel = level;

        // Run the actual test case
        final Logger logger = Logger('test.channel');
        logger.fatal('Message 1');
        logger.fatal('Message 2');
        logger.error('Message 3');
        logger.error('Message 4');
        logger.warning('Message 5');
        logger.warning('Message 6');
        logger.info('Message 7');
        logger.info('Message 8');
        logger.debug('Message 9');
        logger.debug('Message 10');
        logger.trace('Message 11');
        logger.trace('Message 12');

        // Check whether the log output is as expected
        List<String> fileContent = (logConfig.destination as MemoryLogDestination).loggedMessages;

        // Ensure the message count is as expected
        expect(fileContent.length, equals(expectedMessageCount));

        // Ensure that all messages of the activated levels have been written in the correct order
        for (int i = 1; i < expectedMessageCount; i++) {
          expect(fileContent[i - 1], contains('Message $i'));
        }
      });
    }
  });

  /// Ensure that the additional 'error' and 'stackTrace' parameters are forwarded properly with all
  /// logging methods.
  group('crosscuttings.logging.parameters', () {
    _LogFunction getLoggingMethod(LogLevel level, Logger logger) {
      switch (level) {
        case LogLevel.fatal:
          return logger.fatal;
        case LogLevel.error:
          return logger.error;
        case LogLevel.warning:
          return logger.warning;
        case LogLevel.info:
          return logger.info;
        case LogLevel.debug:
          return logger.debug;
        case LogLevel.trace:
          return logger.trace;
        case LogLevel.off:
        case LogLevel.all:
          throw AssertionError('These LogLevels cannot be written into.');
      }
    }

    List<LogLevel> paramTestData = <LogLevel>[
      LogLevel.fatal,
      LogLevel.error,
      LogLevel.warning,
      LogLevel.info,
      LogLevel.debug,
      LogLevel.trace,
    ];
    for (final LogLevel level in paramTestData) {
      test(level, () {
        // Configure the log level
        final LogConfiguration logConfig = LogConfiguration();
        logConfig.globalLevel = LogLevel.all;

        // Run the actual test case
        final Logger logger = Logger('test.channel');
        _LogFunction logFunction = getLoggingMethod(level, logger);
        logFunction('Some dummy txt', _ExampleException(), _ExampleStackTrace());

        // Check that all parameter messages are written
        List<String> fileContent = (logConfig.destination as MemoryLogDestination).loggedMessages;
        expect(fileContent[0], contains(_ExampleException.message));
        expect(fileContent[0], contains(_ExampleStackTrace.message));
      });
    }
  });

  /// Special test cases for the LogConfiguration class
  group('crosscuttings.logging.LogConfiguration', () {
    // Ensures that the LogConfiguration class is really a singleton.
    test('isSingleton', () {
      LogConfiguration logConfig1 = LogConfiguration();
      LogConfiguration logConfig2 = LogConfiguration();

      expect(identical(logConfig1, logConfig2), isTrue);
    });

    // Ensures that all properties of the LogConfiguration class can be set and read again.
    test('accessProperties', () {
      LogConfiguration logConfig = LogConfiguration();

      logConfig.globalLevel = LogLevel.debug;
      expect(logConfig.globalLevel, equals(LogLevel.debug));

      LogDestination noopHandler = BlackholeLogDestination();
      logConfig.destination = noopHandler;
      expect(identical(logConfig.destination, noopHandler), isTrue);
    });
  });

  /// Special test cases to ensure that logging works correctly with all handler implementations
  group('crosscuttings.logging.handlers', () {
    const String exampleMessage = 'Example Message';
    const String exampleChannel = 'test.channel';

    Logger configureLogging(LogDestination destination) {
      final LogConfiguration logConfig = LogConfiguration();
      logConfig.globalLevel = LogLevel.debug;
      logConfig.destination = destination;

      return Logger(exampleChannel);
    }

    /// Test for logging with the Blackhole destination.
    /// This handler shall do nothing, so this test mainly ensures that it does not throw.
    void testBlackholeHandler() {
      Logger logger = configureLogging(BlackholeLogDestination());
      logger.warning(exampleMessage);
    }

    /// Test for logging with the the File destination.
    /// Ensures that a log file is written and contains the sent log message
    void testFileHandler() {
      // Create a log file directory
      const String logFileName = 'testexample.log';
      Directory tempDir = Directory.systemTemp.createTempSync('trad_test_');
      File logFile = File('${tempDir.path}${Platform.pathSeparator}$logFileName');

      // Log a single message
      Logger logger = configureLogging(FileLogDestination(logFile.path));
      logger.warning(exampleMessage);

      // The log file must have been written
      expect(logFile.existsSync(), isTrue);

      // Ensure the file content is as expected
      List<String> fileContent = logFile.readAsLinesSync();
      expect(fileContent.length, equals(1));
      expect(fileContent[0], contains(exampleMessage));
      expect(fileContent[0], contains(exampleChannel));

      // Delete the temporary directory
      tempDir.deleteSync(recursive: true);
    }

    /// Test for logging with the Memory destination.
    /// Ensures that the sent log message is stored within the destination object
    void testMemoryHandler() {
      MemoryLogDestination destination = MemoryLogDestination();
      Logger logger = configureLogging(destination);
      logger.warning(exampleMessage);

      expect(destination.loggedMessages.length, equals(1));
      expect(destination.loggedMessages[0], contains(exampleMessage));
      expect(destination.loggedMessages[0], contains(exampleChannel));
    }

    /// Test for logging with the Console destination.
    /// Ensures that the sent message is really print()ed,
    void testConsoleHandler() {
      expect(() {
        Logger logger = configureLogging(ConsoleLogDestination());
        logger.warning(exampleMessage);
      }, prints(contains(exampleMessage)));
    }

    // Run all the defined test cases
    test('BlackholeLogHandler', testBlackholeHandler);
    test('FileLogHandler', testFileHandler);
    test('MemoryLogHandler', testMemoryHandler);
    test('ConsoleLogHandler', testConsoleHandler);
  });

  /// Special test cases to ensure the correct behaviour in error cases
  group('crosscuttings.logging.errors', () {
    /// Ensures the correct behaviour (ArgumentError) in case of an unknown LogDestination being
    /// used. If this test fails, you probably added a new [LogDestination] class without
    /// providing a corresponding [LogHandler] implementation.
    test('UnknownLogDestination', () {
      final LogConfiguration logConfig = LogConfiguration();
      expect(() {
        logConfig.destination = _UnknownLogDestination();
      }, throwsArgumentError);
    });
  });
}

/// A new LogDestination without a corresponding handler implementation.
/// Used for testing some error behaviour.
class _UnknownLogDestination extends LogDestination {}
