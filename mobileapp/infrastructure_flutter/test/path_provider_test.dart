///
/// Unit tests for the trad.mobileapp.infrastructure_flutter.path_provider library.
///
library;

import 'package:flutter_test/flutter_test.dart';
import 'dart:io';

import 'package:adapters/boundaries/paths.dart';
import 'package:infrastructure_flutter/path_provider.dart';

import 'package:path_provider_platform_interface/path_provider_platform_interface.dart';
import 'package:plugin_platform_interface/plugin_platform_interface.dart';

const String _fakeTempDir = '/fake/dir/temp';
const String _fakeAppDataDir = '/fake/dir/appdata';

/// Unit tests for the SystemPathProvider component class.
void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUpAll(() {
    PathProviderPlatform.instance = _FakePathProviderPlatform();
  });

  /// Ensure that all PathProviderBoundary methods return the expected directory path.
  List<(Future<Directory> Function(PathProviderBoundary), String)> testParams =
      <(Future<Directory> Function(PathProviderBoundary p1), String)>[
        ((PathProviderBoundary pathProvider) => pathProvider.getTempDir(), _fakeTempDir),
        ((PathProviderBoundary pathProvider) => pathProvider.getAppDataDir(), _fakeAppDataDir),
      ];
  for (final (Future<Directory> Function(PathProviderBoundary), String) params in testParams) {
    test(params.$2, () async {
      Future<Directory> Function(PathProviderBoundary) pathProviderCall = params.$1;
      String expectedPath = params.$2;

      PathProviderBoundary pathProvider = SystemPathProvider();
      Directory dir = await pathProviderCall(pathProvider);
      expect(dir.toString(), Directory(expectedPath).toString());
    });
  }
}

/// Fake PathProviderPlatform implementation to make the `path_provider` function return arbitrary
/// strings instead of the real directories.
class _FakePathProviderPlatform extends Fake
    with MockPlatformInterfaceMixin
    implements PathProviderPlatform {
  @override
  Future<String?> getTemporaryPath() async {
    return _fakeTempDir;
  }

  @override
  Future<String?> getApplicationSupportPath() async {
    return _fakeAppDataDir;
  }
}
