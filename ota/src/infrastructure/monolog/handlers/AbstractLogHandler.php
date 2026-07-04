<?php

/**
 * Monolog based implementation of the logging component.
 *
 * This namespace provides a collection of log handlers for different destinations.
 */

namespace trad\infrastructure\monolog\handlers;

use Monolog\Handler\FormattableHandlerInterface;
use Monolog\Handler\HandlerInterface;

/**
 * Common interface of all log handlers.
 * A log handler is the destination to which all log messages are sent (e.g. a file or the UI) and
 * can be given as parameter to setupLogging()). All LogHandlers can work with formatters.
 */
interface AbstractLogHandler extends HandlerInterface, FormattableHandlerInterface {}

?>
