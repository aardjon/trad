<?php

// Boundary interfaces to the `adapters` component.
namespace trad\core\boundaries;

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

?>
