<?php

// Boundary interfaces to the `adapters` component.
namespace trad\core\boundaries;

use trad\core\entities\ArtifactMetadata;
use trad\core\entities\DbArtifact;
use \DateTimeImmutable;

/**
 * Interface to components retrieving routedb artifacts from build servives.
 */
interface DbBuildService
{
    /**
     * Returns the metadata of all routedb artifacts that are newer than the given [$startDate]. If
     * there are no such artifacts, the returned array is empty.
     *
     * @return array<ArtifactMetadata>
     */
    public function getNewerArtifactsMetadata(DateTimeImmutable $startDate): array;

    /**
     * Returns the routedb artifact identified by [$artifactIdentifer].
     *
     * Throws an exception if the artifact doesn't exist.
     */
    public function getArtifactContent(string $artifactIdentifer): DbArtifact;
}

?>
