<?php

// Boundary interfaces to the `adapters` component.
namespace trad\core\boundaries;

use trad\core\entities\RouteDbMetadata;

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

?>
