///
/// Unit tests for the crosscuttings.di library
///

import 'package:crosscuttings/di.dart';
import 'package:test/test.dart';

abstract interface class ExampleInterface1 {}

abstract interface class ExampleInterface2 {}

class ExampleImpl extends ExampleInterface1 {}

/// Unit tests for the crosscuttings.di.DependencyProvider class.
void main() {
  group('crosscuttings.di', () {
    final di = DependencyProvider();

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
      expect(di.provide<ExampleInterface1>(), TypeMatcher<ExampleImpl>());
      expect(di.provide<ExampleInterface2>, throwsStateError);
      // Syntax for custom exceptions:
      // expect(di.provide<ExampleInterface2>, throwsA(isA<StateError>()));
    });
  });
}
