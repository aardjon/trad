<?php

/* Business core of the trad.ota web service. */


// Entity types

/** Metadata describing a single route database file. */
class RouteDbMetadata {
    
    /** Full URL for downloading this route database. */
    public string $downloadUrl;
    
    /** Major schema version of this route database. */
    public int $schemaVersionMajor;
    
    /** Minor schema version of this route database. */
    public int $schemaVersionMinor;
    
    /** Creation date of this route database. */
    public string $creationDate;
    
    /** Constructor for directly initializing all members. */
    public function __construct(string $downloadUrl, int $majorVersion, int $minorVersion, string $creationDate) {
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
     * The return value is an array of strings, representing the (local) file paths.
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
     * The $routeDbMetadata parameter is an array of [RouteDbMetadata] objects.
     */
    public function sendDbMetadata(array $routeDbMetadata);
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
) {
    $collectedMetadata = [];

    foreach ($directoryRepository->getRouteDbFiles() as $routeDbFile) {
        $collectedMetadata[] = $metadataRepository->getRouteDbMetadata($routeDbFile);
    }
    
    $ui->sendDbMetadata($collectedMetadata);
}


?>
