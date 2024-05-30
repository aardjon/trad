///
/// Flutter based implementation of the knowledge base data repository.
///
/// This library is responsible for providing data, but must not contain any business logic. Keep it
/// as dumb as possible!
///
library;

import 'package:adapters/boundaries/repositories.dart';

/// Knowledge base repository implementation that retrieves data stored as application assets.
///
/// Each knowledge base document is a single markdown asset. Furthermore, a special asset contains
/// document metadata (e.g. their titles).
///
/// Please see https://github.github.com/gfm/ for Markdown specification.
///
/// TODO: For now, this is still a stub returning hard coded data.
class KnowledgebaseAssetRepository implements KnowledgebaseRepository {
  @override
  KbRepoDocumentId getHomePageIdentifier() {
    return "/home";
  }

  @override
  String loadDocumentTitle(KbRepoDocumentId identifier) {
    return "Lorem Ipsum";
  }

  @override
  String loadDocumentContent(KbRepoDocumentId identifier) {
    return """
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
    """;
  }
}
