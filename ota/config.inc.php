<?php

/** Static configuration of the trad.ota web service. */
class AppConfig {
    
    /** Path to the directory containing all avilable route database files.
     * 
     * This path must be relative to the 'apivX.php` file, e.g. '../dbfiles'. Do not give an
     * absolute path here!
     */
    public string $CONFIG_DATABASE_FILES_DIRECTORY = 'rdbfiles';
}

?>
