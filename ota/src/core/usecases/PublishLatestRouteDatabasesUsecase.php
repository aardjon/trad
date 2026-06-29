<?php

// Use cases of the OTA web service application.

namespace trad\core\usecases;

use trad\core\boundaries\DbBuildService;
use trad\core\boundaries\DbDirectoryRepository;
use trad\core\boundaries\DbMetadataRepository;
use trad\core\boundaries\PresentationBoundary;
use trad\core\entities\ArtifactMetadata;
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

        $availableRouteDbs = $this->getPublishedRouteDbFiles();
        if (count($availableRouteDbs) == 0) {
            $this->logger->info(
                'No new route databases are available on the build service, stopping'
            );

            return;
        }
        $latestRdbMetadata = $this->findLatestRouteDb($availableRouteDbs);
        $oldestRdbMetadata = $this->findOldestRouteDb($availableRouteDbs);

        $newArtifacts = $this->getNewerUnpublishedArtifacts($latestRdbMetadata);
        $newArtifactsCount = count($newArtifacts);
        if ($newArtifactsCount == 0) {
            $this->logger->warning('No workflow created a route database recently, stopping.');

            return;
        }

        $this->logger->info("Got {$newArtifactsCount} new artifacts, publishing the latest one");
        $latestUnpublishedArtifact = $this->findLatestArtifact($newArtifacts);

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

    /**
     * Return the metadata of already published route databases.
     *
     * @return array<RouteDbMetadata>
     */
    private function getPublishedRouteDbFiles(): array
    {
        $availableRouteDbs = [];
        foreach ($this->directoryRepository->getRouteDbFiles() as $routeDbFile) {
            $availableRouteDbs[] = $this->metadataRepository->getRouteDbMetadata($routeDbFile);
        }

        return $availableRouteDbs;
    }

    /**
     * Find and return the latest routedb from the [$availableRouteDbs] ones.
     *
     * @param array<RouteDbMetadata> $availableRouteDbs
     */
    private function findLatestRouteDb(array $availableRouteDbs): RouteDbMetadata
    {
        assert(! empty($availableRouteDbs));
        $latestRdbMetadata = $availableRouteDbs[0];
        foreach ($availableRouteDbs as $routeDbMetadata) {
            if ($latestRdbMetadata->creationDate < $routeDbMetadata->creationDate) {
                $latestRdbMetadata = $routeDbMetadata;
            }
        }
        $this->logger->debug("Got latest routedb: {$latestRdbMetadata->downloadUrl}");

        return $latestRdbMetadata;
    }

    /**
     * Find and return the oldest routedb from the [$availableRouteDbs] ones.
     *
     * @param array<RouteDbMetadata> $availableRouteDbs
     */
    private function findOldestRouteDb(array $availableRouteDbs): RouteDbMetadata
    {
        assert(! empty($availableRouteDbs));
        $oldestRdbMetadata = $availableRouteDbs[0];
        foreach ($availableRouteDbs as $routeDbMetadata) {
            if ($oldestRdbMetadata->creationDate > $routeDbMetadata->creationDate) {
                $oldestRdbMetadata = $routeDbMetadata;
            }
        }
        $this->logger->debug("Got oldest routedb: {$oldestRdbMetadata->downloadUrl}");

        return $oldestRdbMetadata;
    }

    /**
     * Return all artifacts form the build service that are newer than the provided
     * [$latestRdbMetadata] by at least one day.
     *
     * Adding one day to the search starting date to avoid publishing the same (newest) file again,
     * because there is probably a gap between the DB (from the DB itself) and the artifact (from
     * the build service) creation time.
     *
     * @return array<ArtifactMetadata>
     */
    private function getNewerUnpublishedArtifacts(RouteDbMetadata $latestRdbMetadata): array
    {
        $startDate = $latestRdbMetadata->creationDate->add(new DateInterval('P1D'));

        return $this->buildService->getNewerArtifactsMetadata($startDate);
    }

    /**
     * Find and return the latest available artifact from the given [$availableArtifacts] ones.
     *
     * @param array<ArtifactMetadata> $availableArtifacts
     */
    private function findLatestArtifact(array $availableArtifacts): ArtifactMetadata
    {
        assert(! empty($availableArtifacts));
        $latestUnpublishedArtifact = $availableArtifacts[0];
        foreach ($availableArtifacts as $artifact) {
            if ($latestUnpublishedArtifact->creationDate < $artifact->creationDate) {
                $latestUnpublishedArtifact = $artifact;
            }
        }

        return $latestUnpublishedArtifact;
    }
}

?>
