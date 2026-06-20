<?php

/**
 * Monolog based implementation of the logging component.
 *
 * The contents of this file is not not meant to be used outside the infrastructure\monolog
 * namespace.
 */

namespace trad\infrastructure\monolog\loggers;

use Monolog\Logger as MonoLogger;
use trad\core\logging\Logger as TradLogger;

/**
 * Monolog based Logger implementation.
 * This is a simple wrapper that forwards all calls to the Monolog library.
 *
 * @psalm-api
 */
final class MonologLogger extends TradLogger
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

?>
