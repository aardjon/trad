<?php

// Factory interface for creating new Logger instances.
// Normally, clients should not need to use it directly.

namespace trad\core\logging;

use trad\core\logging\Logger;

/**
 * Interface of a factory for creating Logger instances, used by the Logger::get() method.
 */
interface LoggerFactory
{
    /**
     * Create and return a new Logger instance that sends all messages to the given [$channel].
     */
    public function getLogger(string $channel): Logger;
}

?>
