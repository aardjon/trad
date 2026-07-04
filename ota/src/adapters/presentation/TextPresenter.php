<?php

namespace trad\adapters\presentation;

use trad\core\boundaries\PresentationBoundary;

/**
 * UI implementation that sends plain text to the client.
 */
final class TextPresenter implements PresentationBoundary
{
    public function __construct()
    {
        header('Content-Type: text/plain');
    }

    #[\Override]
    public function sendDbMetadata(array $routeDbMetadata): void
    {
        // Don't write DB metadata into text output (yet)!
    }

    #[\Override]
    public function sendMessage(string $message): void
    {
        echo $message;
    }
}

?>
