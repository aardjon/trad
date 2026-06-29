<?php

// Use cases of the OTA web service application.

namespace trad\core\usecases;

use trad\core\boundaries\DbBuildService;
use trad\core\boundaries\DbDirectoryRepository;
use trad\core\boundaries\DbMetadataRepository;
use trad\core\boundaries\PresentationBoundary;
use trad\core\entities\RouteDbMetadata;
use trad\core\logging\Logger;
use \DateInterval;
use \DateTime;

/**
 * Use case: Publish the latest route database available on the given build service.
 */
final class PublishLatestRouteDatabasesUsecase
{
    private Logger $logger;
    private DbDirectoryRepository $directoryRepository;
    private DbMetadataRepository $metadataRepository;
    private DbBuildService $buildService;

    /**
     * Constructor for creating a new instance.
     *
     * Parameter $directoryRepository: Component for collecting all route database files.
     * Parameter $metadataRepository: Component for reading metadata from a given route database
     *      file.
     * Parameter $buildService: Component for retrieving data from a build service.
     * Parameter $ui: Component for preparing and sending a response to the client.
     */
    public function __construct(
        DbDirectoryRepository $directoryRepository,
        DbMetadataRepository $metadataRepository,
        DbBuildService $buildService,
    ) {
        $this->logger = Logger::get('trad.core.usecases');
        $this->directoryRepository = $directoryRepository;
        $this->metadataRepository = $metadataRepository;
        $this->buildService = $buildService;
    }

    /**
     * Execute this use case.
     */
    public function run(): void
    {
        $this->logger->info('Running use case publishLatestRouteDatabases()');

        // Get the metadata of already published route databases
        /** @var array<RouteDbMetadata> $availableRouteDbs */
        $availableRouteDbs = [];
        foreach ($this->directoryRepository->getRouteDbFiles() as $routeDbFile) {
            $availableRouteDbs[] = $this->metadataRepository->getRouteDbMetadata($routeDbFile);
        }

        if (count($availableRouteDbs) == 0) {
            $this->logger->info(
                'No new route databases are available on the build service, stopping'
            );

            return;
        }

        // Find the newest and the oldest published route db
        $latestRdbMetadata = $availableRouteDbs[0];
        $oldestRdbMetadata = $availableRouteDbs[0];
        foreach ($availableRouteDbs as $routeDbMetadata) {
            if ($latestRdbMetadata->creationDate < $routeDbMetadata->creationDate) {
                $latestRdbMetadata = $routeDbMetadata;
            }
            if ($oldestRdbMetadata->creationDate > $routeDbMetadata->creationDate) {
                $oldestRdbMetadata = $routeDbMetadata;
            }
        }
        $this->logger->info("Got latest routedb: {$latestRdbMetadata->downloadUrl}");

        // Add one day to the search sarting date avoid publishing the same (newst) file again,
        // because there is probably a gap between the DB (from the DB itself) and the artifact
        // (from the build service) creation time.
        $startDate = $latestRdbMetadata->creationDate->add(new DateInterval('P1D'));
        // Now, get the metadata of all newer route databases available on the build service
        $newArtifacts = $this->buildService->getNewerArtifactsMetadata($startDate);
        $newArtifactsCount = count($newArtifacts);
        if ($newArtifactsCount == 0) {
            $this->logger->warning('No workflow created a route database recently, stopping.');

            return;
        }
        $this->logger->info("Got {$newArtifactsCount} new artifacts, publishing the latest one");

        // Find the latest available artifact
        $latestUnpublishedArtifact = $newArtifacts[0];
        foreach ($newArtifacts as $artifact) {
            if ($latestUnpublishedArtifact->creationDate < $artifact->creationDate) {
                $latestUnpublishedArtifact = $artifact;
            }
        }

        $this->logger->info("Downloading latest artifact {$latestUnpublishedArtifact->identifier}");
        $newRouteDbArtifact = $this->buildService->getArtifactContent(
            $latestUnpublishedArtifact->identifier
        );

        $this->logger->info("Publishing artifact {$newRouteDbArtifact->filePath}");
        $this->logger->info("Replacing oldest artifact {$oldestRdbMetadata->downloadUrl}");
        $this->directoryRepository->replaceRouteDb(
            $oldestRdbMetadata->downloadUrl,
            $newRouteDbArtifact->filePath,
        );

        $this->logger->info('Done');
    }
}

?>
