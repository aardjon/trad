<?php

// Use cases of the OTA web service application.

namespace trad\core\usecases;

use trad\core\boundaries\DbDirectoryRepository;
use trad\core\boundaries\DbMetadataRepository;
use trad\core\boundaries\PresentationBoundary;

/**
 * Use case: Client requested the metadata of all available route databases.
 */
final class ProvideAvailableRouteDatabasesUsecase
{
    private DbDirectoryRepository $directoryRepository;
    private DbMetadataRepository $metadataRepository;
    private PresentationBoundary $ui;

    /**
     * Constructor for creating a new instance.
     *
     * Parameter $directoryRepository: Component for collecting all route database files.
     * Parameter $metadataRepository: Component for reading metadata from a given route database file.
     * Parameter $ui: Component for preparing and sending a response to the client.
     */
    public function __construct(
        DbDirectoryRepository $directoryRepository,
        DbMetadataRepository $metadataRepository,
        PresentationBoundary $ui,
    ) {
        $this->directoryRepository = $directoryRepository;
        $this->metadataRepository = $metadataRepository;
        $this->ui = $ui;
    }

    public function run(): void
    {
        $collectedMetadata = [];

        foreach ($this->directoryRepository->getRouteDbFiles() as $routeDbFile) {
            $collectedMetadata[] = $this->metadataRepository->getRouteDbMetadata($routeDbFile);
        }

        $this->ui->sendDbMetadata($collectedMetadata);
    }
}

?>
