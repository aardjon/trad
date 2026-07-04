<?php

/**
 * Monolog based implementation of the logging component.
 *
 * This namespace provides a collection of log handlers for different destinations.
 */

namespace trad\infrastructure\monolog\handlers;

use Monolog\Handler\AbstractProcessingHandler;
use Monolog\Logger as MonoLogger;
use Psr\Log\LogLevel;
use trad\core\boundaries\PresentationBoundary;
use trad\infrastructure\monolog\handlers\AbstractLogHandler;
use \InvalidArgumentException;

/**
 * A handler that sends all log messages to the UI.
 *
 * @phpstan-import-type Level from \Monolog\Logger
 * @phpstan-import-type LevelName from \Monolog\Logger
 * @psalm-api
 */
final class UiLoggingHandler extends AbstractProcessingHandler implements AbstractLogHandler
{
    /**
     * The UI to all log messages shall be sent.
     */
    private PresentationBoundary $uiBoundary;

    /**
     * Create a new UiLoggingHandler instance sending log message to the given UI boundary.
     *
     * The $level and $bubble parameters are forwarded to the Monolog base class, see there for
     * documentation.
     *
     * @param $ui The UI that shall be used for displaying log messages.
     * @param Level|LevelName|LogLevel::* $level See base class for documentation.
     */
    public function __construct(
        PresentationBoundary $ui,
        $level = MonoLogger::DEBUG,
        bool $bubble = true,
    ) {
        parent::__construct($level, $bubble);
        $this->uiBoundary = $ui;
    }

    #[\Override]
    protected function write(array $record): void
    {
        /** @var mixed $formattedRecord */
        $formattedRecord = $record['formatted'];
        if (is_string($formattedRecord)) {
            $this->uiBoundary->sendMessage($formattedRecord);
        } else {
            // Raise to cause an error in the server logfile
            $className = get_debug_type($formattedRecord);
            throw new InvalidArgumentException(
                "Formatted log message must be a string, got: {$className}"
            );
        }
    }
}

?>
