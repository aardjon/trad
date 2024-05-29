///
/// Definition of the boundary between the core and the user interface.
///
library;

import '../entities/knowledgebase.dart';

/// Interface providing user interactions to the core.
///
/// This is the application-wide access point for user interactions.
abstract interface class PresentationBoundary {
  /// Initializes the user interface.
  ///
  /// This may display some kind of "loading" or "splash" screen if appropriate.
  void initUserInterface();

  /// Change the active domain to the *Route Database* domain.
  void switchToRouteDb();

  /// Change the active domain to the *Journal* domain.
  void switchToJournal();

  /// Let the UI display the provided [document] in the *Knowledgebase* domain.
  void showKnowledgebaseDocument(KnowledgebaseDocument document);

  /// Change the active domain to the *About* domain.
  void switchToAbout();
}
