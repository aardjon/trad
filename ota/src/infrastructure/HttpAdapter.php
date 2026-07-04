<?php

namespace trad\infrastructure;

use trad\adapters\boundaries\NetworkAdapter;
use trad\core\logging\Logger;
use \RuntimeException;
use \stdClass;

/**
 * Implementation of HTTP requests using the built-in `curl` library. Besides being a wrapper for
 * `curl`, this component ensures that certain connection settings like timeouts or user agent
 * strings are the same for all HTTP connections.
 */
final class HttpAdapter implements NetworkAdapter
{
    /**
     * Logger to use by this component.
     */
    private Logger $logger;

    /**
     * User agent to send with all HTTP requests.
     */
    private string $userAgent = 'trad.ota';

    /**
     * Constructor creating a new HttpAdapter instance.
     */
    public function __construct()
    {
        $this->logger = Logger::get('trad.infrastructure.http');
    }

    /**
     * The Psalm linter produces false positives for this method when casting to `object` in order
     * to return `stdClass`: https://github.com/vimeo/psalm/issues/8187
     * That's why we ignore them.
     *
     * @psalm-suppress MoreSpecificReturnType,LessSpecificReturnStatement
     */
    #[\Override]
    public function getJsonPayload(
        string $url,
        array $params,
        array $additionalHeaders
    ): stdClass {
        $headers = $this->createHeaders($additionalHeaders);
        $response = $this->request($url, $headers);

        /** @var mixed */
        $jsonData = json_decode($response, false);
        if ($jsonData === null) {
            throw new RuntimeException('Parse error: Invalid JSON data');
        }

        //
        return (object) $jsonData;
    }

    #[\Override]
    public function getBinaryPayload(string $url, array $additionalHeaders): string
    {
        $headers = $this->createHeaders($additionalHeaders);
        $response = $this->request($url, $headers);

        return $response;
    }

    /**
     * Create an array of all HTTP headers that must be sent with the next request. This method
     * combines some hard coded headers (that are always sent) with the given [$additionalHeaders].
     *
     * @param array<int, string> $additionalHeaders Additional, request specific headers
     * @return array<int, string>
     */
    private function createHeaders(array $additionalHeaders): array
    {
        $defaultHeaders = ["User-Agent: {$this->userAgent}"];

        return array_merge($defaultHeaders, $additionalHeaders);
    }

    /**
     * Request the given [$url] via HTTP, sending the given [$headers] and returning the response
     * payload in case of success. Raises if the request failed.
     *
     * @param $url The URL to request, must be a HTTP or HTTPS URL.
     * @param array<int, string> $headers Array of HTTP headers to send.
     */
    private function request(string $url, array $headers): string
    {
        $this->logger->debug("HTTP Request: {$url}");

        $ch = curl_init($url);
        if ($ch === false) {
            throw new RuntimeException(
                'curl initialization failed! Is the extension installed at all?'
            );
        }
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);  // Return the payload
        curl_setopt($ch, CURLOPT_CUSTOMREQUEST, 'GET');
        curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);
        curl_setopt($ch, CURLOPT_FOLLOWLOCATION, true);
        curl_setopt($ch, CURLOPT_MAXREDIRS, 5);
        curl_setopt($ch, CURLOPT_TIMEOUT, 30);
        curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, true);
        curl_setopt($ch, CURLOPT_SSL_VERIFYHOST, 2);

        $payload = curl_exec($ch);
        if ($payload === false) {
            $errnum = curl_errno($ch);
            $this->logger->error("Request error {$errnum}.");
            throw new RuntimeException('HTTP request failed');
        } else if ($payload === true) {
            // true is returned if the query succeeded but the payload is empty
            $payload = '';
        }

        /** @var int|false */
        $statusCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        if ($statusCode === false) {
            throw new RuntimeException('Unable to get HTTP status code from response');
        }
        $this->logger->debug("Got HTTP status code: {$statusCode}");
        if ($statusCode != 200) {
            throw new RuntimeException("Unexpected HTTP response {$statusCode}: {$payload}");
        }

        return $payload;
    }
}

?>
