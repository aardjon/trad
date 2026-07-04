<?php

/**
 * Boundary interface from the `adapters` rings to the networking component in the `infrastructure`
 * ring. Allows to easily mock all network access in unit tests.
 */

namespace trad\adapters\boundaries;

use \stdClass;

/**
 * Interface of a generic networking interface that allows to access remote resources by their URL,
 * via HTTP(S).
 */
interface NetworkAdapter
{
    /**
     * Retrieve and return the (binary) JSON content of the resource at the requested [$url].
     * [$params] are additional parameters to be sent as part of the URL, and will be appended
     * (and encoded) appropriately, while [$additionalHeaders] are sent as together with the request
     * header.
     *
     * @param string $url
     * @param array<string, string> $params
     * @param array<int, string> $additionalHeaders
     *
     * Raises RuntimeException if the resource payload cannot be retrieved (e.g. becuse of network
     * or permission error) or is not a valid JSON resource (i.e. plain text or binary).
     */
    public function getJsonPayload(string $url, array $params, array $additionalHeaders): stdClass;

    /**
     * Retrieve and return the raw binary content of the resource at the requested [$url]. [$params]
     * are additional parameters to be sent as part of the URL, and will be appended (and encoded)
     * appropriately, while [$additionalHeaders] are sent as together with the request header.
     *
     * @param string $url
     * @param array<int, string> $additionalHeaders
     *
     * Raises RuntimeException if the resource payload cannot be retrieved (e.g. becuse of network
     * or permission error).
     */
    public function getBinaryPayload(string $url, array $additionalHeaders): string;
}

?>
