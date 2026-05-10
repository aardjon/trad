<?php

/* Business core of the trad.ota web service. */


// Entity types

/** Metadata describing a single route database file. */
final class RouteDbMetadata {
    
    /** Full URL for downloading this route database. */
    public string $downloadUrl;
    
    /** Major schema version of this route database. */
    public int $schemaVersionMajor;
    
    /** Minor schema version of this route database. */
    public int $schemaVersionMinor;
    
    /** Creation time stamp of this route database. */
    public DateTimeImmutable $creationDate;
    
    /** Constructor for directly initializing all members. */
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



// Component interfaces


/** Interface to components for collecting all available route database files. */
interface DbDirectoryRepository {
    
    /** Return the paths of all available route database files.
     * 
     * @return array<string> The (local) route database file paths.
     */
    public function getRouteDbFiles() : array;
}


/** Interface to components for reading metadata objects from route database files. */
interface DbMetadataRepository {
    
    /** Create a [RouteDbMetadata] describing the route database file given as $routeDbFile. */
    public function getRouteDbMetadata(string $routeDbFile) : RouteDbMetadata;
}


/** Interface to components for presenting data to the client. */
interface PresentationBoundary {
    
    /** Send the given database metadata to the client, in the requested format.
     * 
     * @param array<RouteDbMetadata> $routeDbMetadata Route DB information to be sent.
     */
    public function sendDbMetadata(array $routeDbMetadata) : void;
}



// Use cases


/** Use case: Client requested the metadata of all available route databases.
 * 
 * Parameter $directoryRepository: Component for collecting all route database files.
 * Parameter $metadataRepository: Component for reading metadata from a given route database file.
 * Parameter $ui: Component for preparing and sending a response to the client.
 */
function provideAvailableRouteDatabases(
    DbDirectoryRepository $directoryRepository,
    DbMetadataRepository $metadataRepository,
    PresentationBoundary $ui,
) : void {
    $collectedMetadata = [];

    foreach ($directoryRepository->getRouteDbFiles() as $routeDbFile) {
        $collectedMetadata[] = $metadataRepository->getRouteDbMetadata($routeDbFile);
    }
    
    $ui->sendDbMetadata($collectedMetadata);
}


?>
