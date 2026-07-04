<?php

namespace trad\core\entities;

use \DateTimeImmutable;

/**
 * Metadata describing a single artifact that can be retrieved from a build service. It does not
 * contain the artifact content/data itself.
 */
final class ArtifactMetadata
{
    /**
     * Unique identifier (URI) of this build artifact.
     */
    public string $identifier;

    /**
     * Creation time stamp of this build artifact.
     */
    public DateTimeImmutable $creationDate;

    /**
     * Constructor for directly initializing all members.
     */
    public function __construct(
        string $identifier,
        DateTimeImmutable $creationDate,
    ) {
        $this->identifier = $identifier;
        $this->creationDate = $creationDate;
    }
}

?>
