<?php

require_once('core.php');


class JsonPresenter implements PresentationBoundary {
    public function __construct() {
        header('Content-Type: application/json');
    }
    
    public function sendDbMetadata(array $routeDbMetadata) {
        echo json_encode($routeDbMetadata);
    }
}


?>
