<?php

namespace trad\adapters\presentation;

use trad\core\boundaries\PresentationBoundary;
use \DateTimeInterface;

/**
 * UI implementation that sends JSON data to the client.
 *
 * This UI is not able to display log messages.
 */
final class JsonPresenter implements PresentationBoundary
{
    public function __construct()
    {
        header('Content-Type: application/json');
    }

    #[\Override]
    public function sendDbMetadata(array $routeDbMetadata): void
    {
        $jsonData = [];
        foreach ($routeDbMetadata as $routeDb) {
            $jsonData[] = [
                'downloadUrl' => $routeDb->downloadUrl,
                'schemaVersionMajor' => $routeDb->schemaVersionMajor,
                'schemaVersionMinor' => $routeDb->schemaVersionMinor,
                'creationDate' => $routeDb->creationDate->format(DateTimeInterface::RFC3339_EXTENDED),
            ];
        }
        echo json_encode($jsonData);
    }

    #[\Override]
    public function sendMessage(string $message): void
    {
        // Don't write user messages into the JSON output!
    }
}

?>
