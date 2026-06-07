<?php

// / Boundary interfaces to the `adapters` component.

require_once (__DIR__.'/entities.php');

/**
 * Interface to components for collecting all available route database files.
 */
interface DbDirectoryRepository
{
    /**
     * Return the paths of all available route database files.
     *
     * @return array<string> The (local) route database file paths.
     */
    public function getRouteDbFiles(): array;
}

/**
 * Interface to components for reading metadata objects from route database files.
 */
interface DbMetadataRepository
{
    /**
     * Create a [RouteDbMetadata] describing the route database file given as $routeDbFile.
     */
    public function getRouteDbMetadata(string $routeDbFile): RouteDbMetadata;
}

/**
 * Interface to components for presenting data to the client.
 */
interface PresentationBoundary
{
    /**
     * Send the given database metadata to the client, in the requested format.
     *
     * @param array<RouteDbMetadata> $routeDbMetadata Route DB information to be sent.
     */
    public function sendDbMetadata(array $routeDbMetadata): void;

    /**
     * Send a notification to the client which shall be displayed to the user if possible.
     * Implementations are allowed to ignore these messages if displaying them is not possible or
     * inappropriate, so there is not guarantee that they are really shown to a human!
     */
    public function sendMessage(string $message): void;
}

?>
