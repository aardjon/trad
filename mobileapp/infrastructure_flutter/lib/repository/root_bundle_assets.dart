///
/// Flutter based implementation of an assets repository.
///
/// This library is responsible for providing data, but must not contain any business logic. Keep it
/// as dumb as possible!
///
library;

import 'package:flutter/services.dart' show rootBundle;

import 'package:adapters/boundaries/repositories/assets.dart';

/// Asset repository implementation that retrieves data globally stored as (Flutter) application
/// assets via the root bundle.
class RootBundleAssetRepository implements AssetRepositoryBoundary {
  // Prefix for all AssetIds referring to assets of the [infrastructure_flutter] package.
  static const String _assetPrefix = 'packages/infrastructure_flutter/assets';

  @override
  List<AssetNamespace> getAllNamespaces() {
    return <AssetNamespace>['knowledgebase'];
  }

  @override
  AssetId getMetadataAssetId(AssetNamespace namespace) {
    return '$_assetPrefix/$namespace/index.md';
  }

  @override
  Future<List<String>> loadStringContent(AssetId id) async {
    String assetContent = await rootBundle.loadString(id);
    return assetContent.trim().split('\n');
  }
}
