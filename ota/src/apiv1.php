<?php

/*
 * Main entry point of the trad.ota web service API.
 *
 * This file is the API endpoint to be requested by clients. For each request, it prepares all
 * components necessary for processing it, and starts the correct use case.
 */

namespace trad;

error_reporting(E_ALL);

require_once ('autoload.php');
require_once ('config.inc.php');

use trad\adapters\presentation\JsonPresenter;
use trad\adapters\repositories\FilesystemRepository;
use trad\adapters\repositories\RouteDbFileReader;
use trad\core\usecases\ProvideAvailableRouteDatabasesUsecase;
use trad\infrastructure\monolog\handlers\BlackHoleLoggingHandler;
use trad\infrastructure\monolog\loggers\MonologLoggerFactory;

/**
 * Entry point for handling HTTP GET requests.
 */
function api_get(): void
{
    MonologLoggerFactory::setupLogging(new BlackHoleLoggingHandler());

    $staticConfig = new AppConfig();
    $ui = new JsonPresenter();
    $directoryReader = new FilesystemRepository($staticConfig->CONFIG_DATABASE_FILES_DIRECTORY);
    $metadataReader = new RouteDbFileReader();

    $usecase = new ProvideAvailableRouteDatabasesUsecase($directoryReader, $metadataReader, $ui);
    $usecase->run();
}

api_get();

?>
