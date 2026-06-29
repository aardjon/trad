<?php

namespace trad\core\entities;

use \DateTimeImmutable;

/**
 * Reference to the content of a downloaded build artifact.
 *
 * The artifact is usually stored as a local file, so this reference is basically a link to that.
 */
final class DbArtifact
{
    /**
     * Local path to a file containing the artifact content/payload.
     */
    public string $filePath;

    /**
     * Constructor for directly initializing all members.
     */
    public function __construct(
        string $filePath
    ) {
        $this->filePath = $filePath;
    }
}

?>
