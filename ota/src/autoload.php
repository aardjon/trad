<?php

/**
 * Autoload all project and external modules during startup.
 */

namespace trad;

/**
 * Return the path to the 'vendor' directory (created by composer) from which to load external
 * libraries. The returned path always ends with a path separator.
 *
 * The location differs between dev and prod systems (i.e. undeployed vs. deployed).
 *
 * @throws \RuntimeException if no vendor dir can be found.
 */
function findVendorDir(): string
{
    $currentDir = __DIR__.DIRECTORY_SEPARATOR;

    // Undeployed/dev mode
    $devVendorDir = $currentDir.'..'.DIRECTORY_SEPARATOR.'vendor'.DIRECTORY_SEPARATOR;
    // Deployed/prod mode
    $prodVendorDir = $currentDir.'.vendor'.DIRECTORY_SEPARATOR;

    foreach ([$devVendorDir, $prodVendorDir] as $vendorDir) {
        if (file_exists($vendorDir)) {
            return $vendorDir;
        }
    }
    echo ('Installation seems to be broken.');
    throw new \RuntimeException("Cannot find vendor directory. Did you run 'composer install'?");
}

$vendorDir = findVendorDir();

/**
 * Suppress 'cannot find include' linter error because in this case it cannot be checked statically.
 *
 * @psalm-suppress UnresolvableInclude
 */
require_once ($vendorDir.DIRECTORY_SEPARATOR.'autoload.php');

?>
