///
/// Unit tests for the crosscuttings.logging library.
///
library;

import 'dart:io';

import 'package:test/test.dart';

import 'package:crosscuttings/logging/logger.dart';

/// Unit tests for the crosscuttings.logging component.
void main() {
  /// Test cases for correct level propagation and filtering
  group('crosscuttings.logging.loglevels', () {
    setUp(() {
      // Configure logging to write to a file
      final LogConfiguration logConfig = LogConfiguration();
      logConfig.destination = MemoryLogDestination();
    });

    /// Ensures that all messages matching the log level configuration are be written to the log
    /// file. To achieve this, two messages are written to each level. The [level] parameter
    /// defines the level until which the messages must end up in the file. The
    /// [expectedMessageCount] defines the number of log messages that are expected to end up in
    /// the log file. If not messages are written, the file must not be created at all.
    void runTestCase(LogLevel level, int expectedMessageCount) {
      // Configure the log level
      final LogConfiguration logConfig = LogConfiguration();
      logConfig.globalLevel = level;

      // Run the actual test case
      final Logger logger = Logger("test.channel");
      logger.fatal("Message 1");
      logger.fatal("Message 2");
      logger.error("Message 3");
      logger.error("Message 4");
      logger.warning("Message 5");
      logger.warning("Message 6");
      logger.info("Message 7");
      logger.info("Message 8");
      logger.debug("Message 9");
      logger.debug("Message 10");
      logger.trace("Message 11");
      logger.trace("Message 12");

      // Check whether the log output is as expected
      List<String> fileContent = (logConfig.destination as MemoryLogDestination).loggedMessages;

      // Ensure the message count is as expected
      expect(fileContent.length, equals(expectedMessageCount));

      // Ensure that all messages of the activated levels have been written in the correct order
      for (int i = 1; i < expectedMessageCount; i++) {
        expect(fileContent[i - 1], contains("Message $i"));
      }
    }

    test(
      'AllLevel',
      () => runTestCase(LogLevel.all, 12),
    );
    test(
      'TraceLevel',
      () => runTestCase(LogLevel.trace, 12),
    );
    test(
      'DebugLevel',
      () => runTestCase(LogLevel.debug, 10),
    );
    test(
      'InfoLevel',
      () => runTestCase(LogLevel.info, 8),
    );
    test(
      'WarningLevel',
      () => runTestCase(LogLevel.warning, 6),
    );
    test(
      'ErrorLevel',
      () => runTestCase(LogLevel.error, 4),
    );
    test(
      'FatalLevel',
      () => runTestCase(LogLevel.fatal, 2),
    );
    test(
      'OffLevel',
      () => runTestCase(LogLevel.off, 0),
    );
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
    const String exampleMessage = "Example Message";
    const String exampleChannel = "test.channel";

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
      final String logFileName = "testexample.log";
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
      expect(
        () {
          Logger logger = configureLogging(ConsoleLogDestination());
          logger.warning(exampleMessage);
        },
        prints(contains(exampleMessage)),
      );
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
    /// used. If this tets fails, you probably added a new [LogDestination] class without
    /// providing a corresponding [LogHandler] implementation.
    test('UnknownLogDestination', () {
      final LogConfiguration logConfig = LogConfiguration();
      expect(() {
        logConfig.destination = _UnknownLogDestination();
      }, throwsArgumentError);
    });
  });
}

/// A new LogDestination without a correspoding handler implementation.
/// Used for testing some error behaviour.
class _UnknownLogDestination extends LogDestination {}
