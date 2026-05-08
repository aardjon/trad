<?php

require_once('core.php');


class JsonPresenter implements PresentationBoundary {
    public function __construct() {
        header('Content-Type: application/json');
    }
    
    public function sendDbMetadata(array $routeDbMetadata) {
        $jsonData = [];
        foreach($routeDbMetadata as $routeDb) {
            $jsonData[] = [
                'downloadUrl' => $routeDb->downloadUrl,
                'schemaVersionMajor' => $routeDb->schemaVersionMajor,
                'schemaVersionMinor' => $routeDb->schemaVersionMinor,
                'creationDate' => $routeDb->creationDate->format(DateTimeInterface::RFC3339_EXTENDED),
            ];
        }
        echo json_encode($jsonData);
    }
}


?>
