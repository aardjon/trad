///
/// Flutter based implementation of a BLOB repository.
///
/// This library is responsible for providing data, but must not contain any business logic. Keep it
/// as dumb as possible!
///
library;

import 'package:flutter/services.dart' show rootBundle;

import 'package:adapters/boundaries/repositories/blob.dart';

/// BLOB repository implementation that retrieves data stored as (Flutter) application assets.
// TODO(aardjon): For now, this is just a stub returning hard coded data.
class AssetRepository implements BlobRepositoryBoundary {
  // Prefix for all BlobIds referring to assets of the [infrastructure_flutter] package.
  static const String _assetPrefix = 'packages/infrastructure_flutter/assets';

  @override
  List<BlobNamespace> getAllNamespaces() {
    return <BlobNamespace>['knowledgebase'];
  }

  @override
  BlobId getIndexBlobId(BlobNamespace namespace) {
    return '$_assetPrefix/$namespace/index.md';
  }

  @override
  Future<List<String>> loadStringContent(BlobId id) async {
    String blobContent = await rootBundle.loadString(id);
    return blobContent.trim().split('\n');
  }
}
