///
/// Unit tests for the crosscuttings.di library.
///
library;

import 'package:test/test.dart';

import 'package:crosscuttings/di.dart';

abstract interface class ExampleInterface1 {}

abstract interface class ExampleInterface2 {}

class ExampleImpl implements ExampleInterface1 {}

/// Unit tests for the crosscuttings.di.DependencyProvider class.
void main() {
  group('crosscuttings.di', () {
    final DependencyProvider di = DependencyProvider();

    setUp(() {
      di.register<ExampleInterface1>(() {
        return ExampleImpl();
      });
    });

    tearDown(() async {
      return di.shutdown();
    });

    /// Ensure the correct behaviour of the provide() method:
    ///  - Return the registered implementation, if any
    ///  - Throw if the requested interface has not been registered
    test('testProvide', () {
      expect(di.provide<ExampleInterface1>(), const TypeMatcher<ExampleImpl>());
      expect(di.provide<ExampleInterface2>, throwsStateError);
      // Syntax for custom exceptions:
      // expect(di.provide<ExampleInterface2>, throwsA(isA<StateError>()));
    });

    /// Ensure that all instances share the same DI configuration: A different instance must return
    /// the registered implementation, too.
    test('testSharedConfiguration', () {
      DependencyProvider localDependencyProvider = DependencyProvider();
      expect(
        localDependencyProvider.provide<ExampleInterface1>(),
        const TypeMatcher<ExampleImpl>(),
      );
    });
  });
}
