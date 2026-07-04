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

    /**
     * Replace the published route database file (that can be downloaded via [$toReplaceUrl]) with
     * the route database file [$replaceWithFilePath]: The new file is moved into the repository and
     * will thus be returned from the next [getRouteDbFiles()] call. The old file is deleted and
     * will thus not be returned by [getRouteDbFiles()] anymore. The [$replaceWithFilePath] is
     * deleted.
     *
     * Raises in case of any error.
     */
    public function replaceRouteDb(
        string $toReplaceUrl,
        string $replaceWithFilePath,
    ): void;
}

?>
