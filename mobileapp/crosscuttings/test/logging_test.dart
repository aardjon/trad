// Unit tests for the crosscuttings.di library

import 'dart:io';

import 'package:logging/logging.dart' as loglib;
import 'package:test/test.dart';

import 'package:crosscuttings/logging.dart';
import 'package:crosscuttings/logging/handlers.dart';

abstract interface class ExampleInterface1 {
  bool isSomething();
}

abstract interface class ExampleInterface2 {
  bool isSomethingElse();
}

class ExampleImpl extends ExampleInterface1 {
  @override
  bool isSomething() {
    return true;
  }
}

/// Unit tests for the crosscuttings.logging component.
void main() {
  /// Test cases for correct level propagation and filtering
  group('crosscuttings.logging.loglevels', () {
    Directory? tempDir;
    File? logFile;

    setUp(() {
      // Create a log file directory
      final String logFileName = "testexample.log";
      tempDir = Directory.systemTemp.createTempSync('trad_test_');
      logFile = File('${tempDir!.path}${Platform.pathSeparator}$logFileName');

      // Configure logging to write to a file
      final logConfig = LogConfiguration();
      logConfig.destination = FileLogDestination(logFile!.path);
    });

    tearDown(() {
      tempDir?.deleteSync(recursive: true);
    });

    /// Ensures that all messages matching the log level configuration are be written to the log
    /// file. To achieve this, two messages are written to each level. The [level] parameter
    /// defines the level until which the messages must end up in the file. The
    /// [expectedMessageCount] defines the number of log messages that are expected to end up in
    /// the log file. If not messages are written, the file must not be created at all.
    void runTestCase(LogLevel level, int expectedMessageCount) {
      // Configure the log level
      final logConfig = LogConfiguration();
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

      // The log file must only be created if messages are written at all
      if (expectedMessageCount > 0) {
        // Ensure that the log file has been written at all
        expect(logFile!.existsSync(), isTrue);

        // Read the created log file
        List<String> fileContent = logFile!.readAsLinesSync();

        // Ensure the message count is as expected
        expect(fileContent.length, equals(expectedMessageCount));

        // Ensure that all messages of the activated levels have been written in the correct
        // order
        for (int i = 1; i < expectedMessageCount; i++) {
          expect(fileContent[i - 1], contains("Message $i"));
        }
      } else {
        // No messages should have been written, so there shoiuldn't be a log file at all
        expect(logFile!.existsSync(), isFalse);
      }
    }

    test('AllLevel', () => runTestCase(LogLevel.all, 12));
    test('TraceLevel', () => runTestCase(LogLevel.trace, 12));
    test('DebugLevel', () => runTestCase(LogLevel.debug, 10));
    test('InfoLevel', () => runTestCase(LogLevel.info, 8));
    test('WarningLevel', () => runTestCase(LogLevel.warning, 6));
    test('ErrorLevel', () => runTestCase(LogLevel.error, 4));
    test('FatalLevel', () => runTestCase(LogLevel.fatal, 2));
    test('OffLevel', () => runTestCase(LogLevel.off, 0));
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

  /// Special test cases for testing the concrete handler implementations only
  group('crosscuttings.logging.handlers', () {
    Directory? tempDir;
    File? logFile;

    setUp(() {
      // Create a log file directory
      final String logFileName = "testexample.log";
      tempDir = Directory.systemTemp.createTempSync('trad_test_');
      logFile = File('${tempDir!.path}${Platform.pathSeparator}$logFileName');
    });

    tearDown(() {
      tempDir?.deleteSync(recursive: true);
    });

    loglib.LogRecord exampleRecord = loglib.LogRecord(
      loglib.Level.SEVERE,
      "Example Message",
      "test.channel",
    );

    /// Test for the BlackholeLogHandler class.
    /// This handler shall do nothing, so this test mainly ensures that it does not throw.
    void testBlackholeHandler() {
      LogHandler handler = BlackholeLogHandler();
      handler.handleRecord(exampleRecord);
    }

    /// Test for the FileLogHandler class.
    /// Ensures that a log file is written and contains the sent log message
    void testFileHandler() {
      LogHandler handler = FileLogHandler(logFile!.path);
      handler.handleRecord(exampleRecord);

      // The log file must have been written
      expect(logFile!.existsSync(), isTrue);

      // Ensure the file content is as expected
      List<String> fileContent = logFile!.readAsLinesSync();
      expect(fileContent.length, equals(1));
      expect(fileContent[0], contains(exampleRecord.loggerName));
      expect(fileContent[0], contains(exampleRecord.message));
    }

    test('BlackholeLogHandler', testBlackholeHandler);
    test('FileLogHandler', testFileHandler);
  });
}
