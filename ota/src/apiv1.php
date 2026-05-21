<?php

/*
 * Main entry point of the trad.ota web service API.
 *
 * This file is the API endpoint to be requested by clients. For each request, it prepares all
 * components necessary for processing it, and starts the correct use case.
 */

error_reporting(E_ALL);

require_once ('config.inc.php');

require_once (__DIR__.'/core/usecases.php');
require_once (__DIR__.'/adapters/repositories/filesystem.php');
require_once (__DIR__.'/adapters/repositories/routedbv1.php');
require_once (__DIR__.'/adapters/presentation.php');

/**
 * Entry point for handling HTTP GET requests.
 */
function api_get(): void
{
    $staticConfig = new AppConfig();
    $directoryReader = new DbDirectoryReader($staticConfig->CONFIG_DATABASE_FILES_DIRECTORY);
    $metadataReader = new TradRouteDbFileReader();
    $ui = new JsonPresenter();

    provideAvailableRouteDatabases($directoryReader, $metadataReader, $ui);
}

api_get();

?>
