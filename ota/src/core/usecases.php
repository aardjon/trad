<?php

// / Use cases of the OTA web service application.

require_once (__DIR__.'/entities.php');

/**
 * Use case: Client requested the metadata of all available route databases.
 *
 * Parameter $directoryRepository: Component for collecting all route database files.
 * Parameter $metadataRepository: Component for reading metadata from a given route database file.
 * Parameter $ui: Component for preparing and sending a response to the client.
 */
function provideAvailableRouteDatabases(
    DbDirectoryRepository $directoryRepository,
    DbMetadataRepository $metadataRepository,
    PresentationBoundary $ui,
): void {
    $collectedMetadata = [];

    foreach ($directoryRepository->getRouteDbFiles() as $routeDbFile) {
        $collectedMetadata[] = $metadataRepository->getRouteDbMetadata($routeDbFile);
    }

    $ui->sendDbMetadata($collectedMetadata);
}

?>
