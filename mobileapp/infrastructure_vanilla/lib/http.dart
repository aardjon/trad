///
/// Implementation of the 'network' component.
///
library;

import 'dart:typed_data';
import 'package:http/http.dart' as http;

import 'package:adapters/boundaries/network.dart';

/// Implementation of the HTTP network boundary, based on the 'http' package.
///
/// This implementation encapsulates the `http` package and therefore all its details. Its methods
/// usually do a HTTP(S) request and return the response content/body without further processing.
class HttpNetworkRequests implements HttpNetworkingBoundary {
  /// Numeric HTTP response status code of successful requests.
  static const int _httpStatusOk = 200;

  /// The HTTP header key defining the content MIME type.
  static const String _contentTypeHeader = 'Content-Type';

  /// HTTP Client to be used by this class instance. Allows unit tests to inject a mocked client.
  final http.Client _httpClient;

  /// Constructor for creating a new HttpNetworkRequests component. The [client] parameter allows
  /// easy mocking of the underlying client implementation e.g. for unit testing, but is not meant
  /// to be used in regular production code.
  HttpNetworkRequests({http.Client? client}) : _httpClient = client ?? http.Client();

  @override
  Future<String> retrieveJsonResource(Uri url) async {
    const String jsonMimeMype = 'application/json';

    http.Response response = await _httpClient.get(url);
    if (response.statusCode != _httpStatusOk) {
      throw HttpRequestException(response.statusCode, response.reasonPhrase ?? '');
    }

    String contentTypeHeader = '';
    for (final MapEntry<String, String> item in response.headers.entries) {
      if (item.key.toLowerCase() == _contentTypeHeader.toLowerCase()) {
        contentTypeHeader = item.value.toLowerCase();
        break;
      }
    }
    if (contentTypeHeader != jsonMimeMype) {
      // Possible reasons: Either the Content-Type header is missing, or it defines a different type
      throw UnexpectedContentTypeException(
        expectedContentType: jsonMimeMype,
        actualContentType: contentTypeHeader,
      );
    }
    return response.body;
  }

  @override
  Future<Uint8List> retrieveBinaryResource(Uri url) async {
    http.Response response = await _httpClient.get(url);
    if (response.statusCode != _httpStatusOk) {
      throw HttpRequestException(response.statusCode, response.reasonPhrase ?? '');
    }
    return response.bodyBytes;
  }
}
