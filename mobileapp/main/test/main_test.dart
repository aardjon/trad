///
/// Unit test for the main.main library
///
library;

import 'package:test/test.dart';

import 'package:core/boundaries/presentation.dart';
import 'package:core/boundaries/storage/knowledgebase.dart';
import 'package:core/boundaries/storage/routedb.dart';
import 'package:crosscuttings/di.dart';
import 'package:main/main.dart';

/// Unit tests for the main.main.ApplicationBootstrap class.
void main() {
  /// Ensure that at least some of the main dependencies have been initialised, i.e. that
  /// initApp() did anything at all:
  ///  - A presentation boundary
  ///  - A routedb storage boundary
  ///  - A knowledge base boundary
  test('main.main.ApplicationBootstrap.initApp', () {
    ApplicationBootstrap bootstrap = ApplicationBootstrap();
    bootstrap.initApp();

    // Retrieving the required dependencies must not throw an error.
    DependencyProvider di = DependencyProvider();
    expect(() => di.provide<PresentationBoundary>(), returnsNormally);
    expect(() => di.provide<RouteDbStorageBoundary>(), returnsNormally);
    expect(() => di.provide<KnowledgebaseStorageBoundary>(), returnsNormally);
  });
}
