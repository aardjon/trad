///
/// Dependency injection library to be used by all parts of the trad application.
///
library;

import 'package:get_it/get_it.dart';

/// Central entry point for registering or retrieving the concrete boundary implementations.
///
/// Usage example:
/// ```dart
/// DependencyProvider di = DependencyProvider();
/// JournalStorageBoundary journalStorage = di.provide<JournalStorageBoundary>();
/// ```
///
/// This class is not a singleton but all instances share the same DI configuration, so they can be
/// created on demand as needed. Most system parts will only ever need the [provide()] method.
class DependencyProvider {
  /// Global GetIt instance to delegate calls to.
  final GetIt _getIt = GetIt.instance;

  /// Returns the concrete implementation for the interface requested by [T].
  ///
  /// Throws [StateError] if the requested interface has not been [register()]ed before.
  T provide<T extends Object>() {
    return _getIt.get<T>();
  }

  /// Registers a new implementation for the interface [T].
  ///
  /// The [instanceFactory] is a functor that must return a new instance of [T]. It will be called
  /// at any time, at the latest when the instance requested via [provide()]. Any previous
  /// implementation registration is discarded.
  ///
  /// Registration should be done only once during start up from within `trad.main`.
  void register<T extends Object>(T Function() instanceFactory) {
    _getIt.registerFactory<T>(instanceFactory);
  }

  /// Cleans up the DI registry by removing all registrations at once.
  ///
  /// This should only be called during shutdown from within `trad.main`.
  Future<void> shutdown() {
    return _getIt.reset(dispose: true);
  }
}
