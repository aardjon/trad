///
/// Boundary interface from the `adapters` rings to the network component in the `infrastructure`
/// ring. Allows to easily mock all network access in unit tests.
///
library;

import 'dart:typed_data';

/// Interface of a generic networking interface that allows to access remote resources by their URL
/// via HTTP(S).
abstract interface class HttpNetworkingBoundary {
  /// Retrieve and return the JSON content of the resource at the requested [url].
  ///
  /// Raises HttpRequestException in case of network or server problems, such as:
  ///  - Connection problem
  ///  - Connection timeout
  ///  - Resource not available
  ///
  /// Raises UnexpectedContentTypeException if the server response is of a wrong (i.e. non-JSON)
  /// content type.
  Future<String> retrieveJsonResource(Uri url);

  /// Retrieve and return the (binary) content of the resource at the requested [url].
  /// Raises HttpRequestException in case of problems, such as:
  ///  - Connection problem
  ///  - Connection timeout
  ///  - Resource not available
  Future<Uint8List> retrieveBinaryResource(Uri url);
}

/// Raised when an HTTP(S) request fails. This can be caused by e.g. network problems, address
/// resolution failures or HTTP errors.
class HttpRequestException implements Exception {
  /// The HTTP response status code
  final int statusCode;

  /// The reason string sent with the response (may be empty)
  final String statusReason;

  /// Constructor for directly initializing all members.
  HttpRequestException(this.statusCode, this.statusReason);

  @override
  String toString() {
    return 'Unexpected HTTP response $statusCode: $statusReason';
  }
}

/// Raised when a successful HTTP(S) request returned a response of an unexpected content type, like
/// e.g. plain text or binary instead of JSON.
class UnexpectedContentTypeException implements Exception {
  /// The expected content MIME type.
  final String expectedContentType;

  /// The actual content MIME type.
  final String actualContentType;

  /// Constructor for directly initializing all members.
  UnexpectedContentTypeException({
    required this.expectedContentType,
    required this.actualContentType,
  });

  @override
  String toString() {
    return "'Expected '$expectedContentType' but got '$actualContentType'";
  }
}
