<?php
// /
// / Entity types of the OTA core component
// /

/**
 * Metadata describing a single route database file.
 */
final class RouteDbMetadata
{
    /**
     * Full URL for downloading this route database.
     */
    public string $downloadUrl;

    /**
     * Major schema version of this route database.
     */
    public int $schemaVersionMajor;

    /**
     * Minor schema version of this route database.
     */
    public int $schemaVersionMinor;

    /**
     * Creation time stamp of this route database.
     */
    public DateTimeImmutable $creationDate;

    /**
     * Constructor for directly initializing all members.
     */
    public function __construct(
        string $downloadUrl,
        int $majorVersion,
        int $minorVersion,
        DateTimeImmutable $creationDate,
    ) {
        $this->downloadUrl = $downloadUrl;
        $this->schemaVersionMajor = $majorVersion;
        $this->schemaVersionMinor = $minorVersion;
        $this->creationDate = $creationDate;
    }
}

?>
