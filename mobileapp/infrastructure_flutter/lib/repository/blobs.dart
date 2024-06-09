///
/// Flutter based implementations of BLOB repositories.
///
/// This library is responsible for providing data, but must not contain any business logic. Keep it
/// as dumb as possible!
///
library;

import 'package:adapters/boundaries/repositories.dart';

/// BLOB repository implementation that retrieves data stored as (Flutter) application assets.
// TODO(aardjon): For now, this is just a stub returning hard coded data.
class AssetRepository implements BlobRepositoryBoundary {
  @override
  List<BlobNamespace> getAllNamespaces() {
    return <BlobNamespace>["/knowledgebase"];
  }

  @override
  BlobId getIndexBlobId(BlobNamespace namespace) {
    return "$namespace/index";
  }

  @override
  List<String> loadStringContent(BlobId id) {
    return """
# Lorem ipsum

# Text block
Lorem ipsum dolor sit amet, consetetur sadipscing elitr, sed diam nonumy eirmod tempor invidunt ut
labore et dolore magna aliquyam erat, sed diam voluptua. At vero eos et accusam et justo duo dolores
et ea rebum. Stet clita kasd gubergren, no sea takimata sanctus est Lorem ipsum dolor sit amet.
Lorem ipsum dolor sit amet, consetetur sadipscing elitr, sed diam nonumy eirmod tempor invidunt ut
labore et dolore magna aliquyam erat, sed diam voluptua. At vero eos et accusam et justo duo
dolores et ea rebum. Stet clita kasd gubergren, no sea takimata sanctus est Lorem ipsum dolor sit
amet.

# Bullet list
 - List item 1
 - List item 2
   - List item 2.1
   - List item 2.2
 - List item 3

# Link test
 [Link Text](/kb/regulations)
    """
        .trim()
        .split("\n");
  }
}
