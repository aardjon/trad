<?php

/**
 * Monolog based implementation of the logging component.
 *
 * This namespace provides a collection of log handlers for different destinations.
 */

namespace trad\infrastructure\monolog\handlers;

use Monolog\Handler\FormattableHandlerTrait;
use Monolog\Handler\NullHandler;
use trad\infrastructure\monolog\handlers\AbstractLogHandler;

/**
 * A (noop) handler for absorbing all messages and never logging anything.
 *
 * Can be used as default or to definitely disable all logging. However, to disable logging it is
 * usually better to set the log level to `LogLevel.off` because this will avoid some overhead like
 * message string creation and propagation and therefore improve performance.
 *
 * @psalm-api
 */
final class BlackHoleLoggingHandler extends NullHandler implements AbstractLogHandler
{
    use FormattableHandlerTrait;
}

?>
