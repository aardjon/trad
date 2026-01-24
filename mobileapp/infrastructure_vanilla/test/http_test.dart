///
/// Unit tests for the 'trad.infrastructure_vanilla.http' module.
///
library;

import 'dart:typed_data';

import 'package:adapters/boundaries/network.dart';
import 'package:http/http.dart' as http;
import 'package:mocktail/mocktail.dart';
import 'package:test/test.dart';

import 'package:infrastructure_vanilla/http.dart';

/// Unit tests for the HttpNetworkRequests component.
// TODO(aardjon): Please add tests that simulate a connection/network failure
void main() {
  /// Ensure that the retrieveJsonResource() method requests the given URL exactly once, and
  /// returns the expected binary data.
  test('retrieveJsonResource() happy path', () async {
    final Uri jsonUri = Uri.https('localhost', 'path/to/json/api');
    const String jsonResponseBody = '[]';
    final http.Response response = http.Response(
      jsonResponseBody,
      200,
      headers: <String, String>{'Content-Type': 'application/json'},
    );

    _HttpClientMock mockedHttpClient = _HttpClientMock();
    when(() => mockedHttpClient.get(jsonUri)).thenAnswer((_) async {
      return response;
    });

    HttpNetworkRequests httpRequests = HttpNetworkRequests(client: mockedHttpClient);
    String jsonData = await httpRequests.retrieveJsonResource(jsonUri);

    // Make sure the given URL was requested exactly once
    verify(() => mockedHttpClient.get(jsonUri)).called(1);

    // Make sure the expected response body was returned
    expect(jsonData, jsonResponseBody);
  });

  /// Ensure that the retrieveBinaryResource() method requests the given URL exactly once, and
  /// returns the expected binary data.
  test('retrieveBinaryResource() happy path', () async {
    final Uri binaryUri = Uri.https('localhost', 'path/to/binary');
    final List<int> binaryResponseBody = <int>[9, 8, 7, 1, 2, 3];
    final http.Response response = http.Response.bytes(
      binaryResponseBody,
      200,
      headers: <String, String>{'Content-Type': 'application/json'},
    );

    _HttpClientMock mockedHttpClient = _HttpClientMock();
    when(() => mockedHttpClient.get(binaryUri)).thenAnswer((_) async {
      return response;
    });

    HttpNetworkRequests httpRequests = HttpNetworkRequests(client: mockedHttpClient);
    Uint8List binaryData = await httpRequests.retrieveBinaryResource(binaryUri);

    // Make sure the given URL was requested exactly once
    verify(() => mockedHttpClient.get(binaryUri)).called(1);

    // Make sure the expected response body was returned
    expect(binaryData, binaryResponseBody);
  });

  /// Ensure that the retrieveJsonResource() throws a HttpRequestException in case of errors:
  ///  - if the server responded with a non-200 status code
  ///  - the response is of a different MIME type
  List<(String, int, Map<String, String>, Type)> testParams =
      <(String, int, Map<String, String>, Type)>[
        (
          'Non-OK status code',
          404,
          <String, String>{'Content-Type': 'application/json'},
          HttpRequestException,
        ),
        (
          'Wrong MIME type',
          200,
          <String, String>{'Content-Type': 'text/plain'},
          UnexpectedContentTypeException,
        ),
      ];
  for (final (String, int, Map<String, String>, Type) params in testParams) {
    final String testLabel = params.$1;
    final int responseStatusCode = params.$2;
    final Map<String, String> responseHeaders = params.$3;
    final Type expectedExceptionType = params.$4;

    test('retrieveJsonResource() error: $testLabel', () async {
      final Uri jsonUri = Uri.https('localhost', 'path/to/json/api');
      final http.Response response = http.Response(
        '',
        responseStatusCode,
        headers: responseHeaders,
      );

      _HttpClientMock mockedHttpClient = _HttpClientMock();
      when(() => mockedHttpClient.get(jsonUri)).thenAnswer((_) async {
        return response;
      });

      // Make sure the requests raises the expected exception
      HttpNetworkRequests httpRequests = HttpNetworkRequests(client: mockedHttpClient);
      expect(() async {
        await httpRequests.retrieveJsonResource(jsonUri);
      }, throwsA(predicate((Object? e) => e.runtimeType == expectedExceptionType)));
    });
  }

  /// Ensure that the retrieveBinaryResource() throws a HttpRequestException in case of errors:
  ///  - if the server responded with a non-200 status code
  test('retrieveBinaryResource() request error', () async {
    final Uri binaryUri = Uri.https('localhost', 'path/to/binary');
    final http.Response response = http.Response('Not OK', 401);

    _HttpClientMock mockedHttpClient = _HttpClientMock();
    when(() => mockedHttpClient.get(binaryUri)).thenAnswer((_) async {
      return response;
    });

    // Make sure the requests raises
    HttpNetworkRequests httpRequests = HttpNetworkRequests(client: mockedHttpClient);
    expect(() async {
      await httpRequests.retrieveBinaryResource(binaryUri);
    }, throwsA(isA<HttpRequestException>()));
  });
}

class _HttpClientMock extends Mock implements http.Client {}
