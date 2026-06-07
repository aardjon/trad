<?php

/**
 * Monolog based implementation of the logging component.
 *
 * This module provides the setup function, a collection of log handlers and of course the actual
 * Logger implementation.
 *
 * To initialize, call setupLogging() once with the desired log handler.
 */
require_once __DIR__.'/../../vendor/autoload.php';
require_once (__DIR__.'/../core/boundaries.php');

use Monolog\Formatter\LineFormatter;
use Monolog\Handler\AbstractProcessingHandler;
use Monolog\Handler\FormattableHandlerInterface;
use Monolog\Handler\FormattableHandlerTrait;
use Monolog\Handler\HandlerInterface;
use Monolog\Handler\NullHandler;
use Monolog\Logger as MonoLogger;
use Psr\Log\LogLevel;

/**
 * Initialize and setup the logging system to use the provided [logHandler].
 *
 * Must be called exactly once at startup.
 */
function setupLogging(AbstractLogHandler $logHandler): void
{
    Logger::setLoggerFactory(new MonologLoggerFactory($logHandler));
}

// /////////////////////////////////////////////////////////////////////////////////////////////////
// Log handlers that can be used as a message destination (parameter to setupLogging()).
// /////////////////////////////////////////////////////////////////////////////////////////////////

/**
 * Common interface of all log handlers.
 * A log handler is the destination to which all log messages are sent (e.g. a file or the UI). All
 * LogHandlers can work with formatters.
 */
interface AbstractLogHandler extends HandlerInterface, FormattableHandlerInterface {}

/**
 * A (noop) handler for absorbing all messages and never logging anything.
 *
 * Can be used as default or to definitely disable all logging. However, to disable logging it is
 * usually better to set the log level to `LogLevel.off` because this will avoid some overhead like
 * message string creation and propagation and therefore improve performance.
 */
final class BlackHoleLoggingHandler extends NullHandler implements AbstractLogHandler
{
    use FormattableHandlerTrait;
}

// /////////////////////////////////////////////////////////////////////////////////////////////////
// Internal: Monolog based Logger and LoggerFactory implementations.
// These classes are not not meant to be used outside this file.
// /////////////////////////////////////////////////////////////////////////////////////////////////

/**
 * Monolog based Logger implementation.
 * This is a simple wrapper that forwards all calls to the Monolog library.
 *
 * @psalm-api
 */
final class MonologLogger extends Logger
{
    private MonoLogger $logger;

    public function __construct(MonoLogger $logger)
    {
        $this->logger = $logger;
    }

    #[\Override]
    public function fatal(string $message): void
    {
        $this->logger->critical($message);
    }

    #[\Override]
    public function error(string $message): void
    {
        $this->logger->error($message);
    }

    #[\Override]
    public function warning(string $message): void
    {
        $this->logger->warning($message);
    }

    #[\Override]
    public function info(string $message): void
    {
        $this->logger->info($message);
    }

    #[\Override]
    public function debug(string $message): void
    {
        $this->logger->debug($message);
    }
}

/**
 * Monolog based LoggerFactory implementation.
 * This factory creates MonologLogger instances.
 */
final class MonologLoggerFactory implements LoggerFactory
{
    private AbstractLogHandler $logHandler;

    public function __construct(AbstractLogHandler $logHandler)
    {
        $this->logHandler = $logHandler;
        $outputFormat = "[%datetime%][%level_name%][%channel%] %message% %context% %extra%\n";
        $this->logHandler->setFormatter(
            new LineFormatter($outputFormat, 'Y-m-d h:m:s', false, true)
        );
    }

    #[\Override]
    public function getLogger(string $channel): Logger
    {
        $logger = new MonoLogger($channel);
        $logger->pushHandler($this->logHandler);

        return new MonologLogger($logger);
    }
}

?>
