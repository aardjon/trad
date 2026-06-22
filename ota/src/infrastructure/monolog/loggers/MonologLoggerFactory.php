<?php

/**
 * Monolog based implementation of the logging component.
 *
 * The contents of this file is not not meant to be used outside the infrastructure\monolog
 * namespace.
 */

namespace trad\infrastructure\monolog\loggers;

use Monolog\Formatter\LineFormatter;
use Monolog\Logger as MonoLogger;
use Psr\Log\LogLevel;
use trad\core\logging\Logger as TradLogger;
use trad\core\logging\LoggerFactory;
use trad\infrastructure\monolog\handlers\AbstractLogHandler;

/**
 * Monolog based LoggerFactory implementation.
 * This factory creates MonologLogger instances.
 */
final class MonologLoggerFactory implements LoggerFactory
{
    private AbstractLogHandler $logHandler;

    /**
     * Initialize and setup the logging system to use the provided [logHandler].
     *
     * Must be called exactly once at startup.
     *
     * @psalm-api
     */
    public static function setupLogging(AbstractLogHandler $logHandler): void
    {
        TradLogger::setLoggerFactory(new MonologLoggerFactory($logHandler));
    }

    /**
     * Shutdown the logging system.
     *
     * After that, no log messages can be processed anymore. This is mainly there for allowing a
     * clean shutdown between unit test cases.
     *
     * @psalm-api
     */
    public static function shutdownLogging(): void
    {
        TradLogger::discardLoggerFactory();
    }

    /**
     * Constructor for creating a new logger factory which uses the given [$logHandler].
     */
    public function __construct(AbstractLogHandler $logHandler)
    {
        $this->logHandler = $logHandler;
        $outputFormat = "[%datetime%][%level_name%][%channel%] %message% %context% %extra%\n";
        $this->logHandler->setFormatter(
            new LineFormatter($outputFormat, 'Y-m-d h:m:s', false, true)
        );
    }

    #[\Override]
    public function getLogger(string $channel): TradLogger
    {
        $logger = new MonoLogger($channel);
        $logger->pushHandler($this->logHandler);

        return new MonologLogger($logger);
    }
}

?>
