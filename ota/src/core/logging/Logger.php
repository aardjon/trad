<?php

// Logging library that can be used by all parts of the trad application.
// Usage:
// - Create a Logger by calling [Logger::get()].
// - Log a message by calling one of the channel functions (e.g. `warning()`) of the Logger
//   instance.
namespace trad\core\logging;

use trad\core\logging\LoggerFactory;
use \RuntimeException;

/**
 * Logger for writing messages to a certain channel.
 *
 * Instances are created with the static [get()] function. Each instance writes to the channel
 * identified by the name given on creation. It's okay to have several [Logger] instances writing
 * to the same channel. A good practise is to create one [Logger] per source file.
 *
 * Usage example:
 * ```php
 * $logger = Logger::get('trad.core.example');
 * $logger->info('Created the first logger');
 * ```
 *
 * Before the first usage, the LoggerFactory to use must be configured by calling
 * [setLoggerFactory()] exactly once.
 *
 * @psalm-api
 */
abstract class Logger
{
    /**
     * The factory to use for creating new Logger instances. Null before initialization.
     */
    private static ?LoggerFactory $loggerFactory = null;

    /**
     * /** Configures the logger factory to use for creating new Logger instances.
     *
     * Must be called exactly once before the very first Logger can be created. Calling it a second
     * time raises an error.
     */
    public static function setLoggerFactory(LoggerFactory $loggerFactory): void
    {
        if (self::$loggerFactory === null) {
            self::$loggerFactory = $loggerFactory;
        } else {
            throw new RuntimeException('The Logger factory has already been configured!');
        }
    }

    /**
     * Creates a new [Logger] which sends its messages to the channel with the provided
     * [$channel].
     *
     * The [$channel] must start with `trad` and reflect the source/architectural position of the
     * module the `Logger` instance is created in, using single dots as delimeters (e.g.
     * `trad.core.usecases.journal`). This makes it easy to filter for messages from a certain
     * system  part later on.
     */
    public static function get(string $channel): Logger
    {
        if (! (self::$loggerFactory === null)) {
            return self::$loggerFactory->getLogger($channel);
        } else {
            throw new RuntimeException('The Logger factory has not been configured!');
        }
    }

    /**
     * Logs a [$message] on the `fatal` level.
     * Example: A critial error that may cause the program to stop running.
     */
    public abstract function fatal(string $message): void;

    /**
     * Logs a [$message] on the `error` level.
     * Example: Some function could not be performed because of a serious problem.
     */
    public abstract function error(string $message): void;

    /**
     * Logs a [$message] on the `warning` level.
     * Example: Something unexpected happened or a problem might occur in the near future, but the
     * software is still working as expected.
     */
    public abstract function warning(string $message): void;

    /**
     * Logs a [$message] on the `info` level.
     * Example: Information that things are working as expected.
     */
    public abstract function info(string $message): void;

    /**
     * Logs a [$message] on the `debug` level.
     * Example: Some detailed information, typically only of interest to a developer trying to
     * diagnose a problem.
     */
    public abstract function debug(string $message): void;
}

?>
