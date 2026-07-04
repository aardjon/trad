<?php

declare(strict_types=1);

/*
 * Main entry point of the trad.ota web service API.
 *
 * This file is the API endpoint to trigger the deployment of the latest the route database,
 * created by some build service. For each request, it prepares all components necessary for
 * processing it, and starts the correct use case.
 */

namespace trad;

error_reporting(E_ALL);

require_once ('autoload.php');
require_once ('config.inc.php');

use trad\adapters\presentation\TextPresenter;
use trad\adapters\repositories\github\GithubBuildService;
use trad\adapters\repositories\FilesystemRepository;
use trad\adapters\repositories\RouteDbFileReader;
use trad\core\usecases\PublishLatestRouteDatabasesUsecase;
use trad\infrastructure\monolog\handlers\UiLoggingHandler;
use trad\infrastructure\monolog\loggers\MonologLoggerFactory;
use trad\infrastructure\HttpAdapter;

/**
 * Entry point for handling HTTP GET requests.
 */
function api_get(): void
{
    $ui = new TextPresenter();
    MonologLoggerFactory::setupLogging(new UiLoggingHandler($ui));

    $staticConfig = new AppConfig();
    $filesystemRepository = new FilesystemRepository($staticConfig->CONFIG_DATABASE_FILES_DIRECTORY);
    $metadataRepository = new RouteDbFileReader();
    $networkAdapter = new HttpAdapter();
    $buildService = new GithubBuildService(
        $networkAdapter,
        $staticConfig->CONFIG_GITHUB_REPO_OWNER,
        $staticConfig->CONFIG_GITHUB_REPO_NAME,
        $staticConfig->CONFIG_GITHUB_API_TOKEN,
    );

    $usecase = new PublishLatestRouteDatabasesUsecase(
        $filesystemRepository,
        $metadataRepository,
        $buildService,
    );
    $usecase->run();
}

api_get();

?>
