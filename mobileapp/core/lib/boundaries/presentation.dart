///
/// Definition of the boundary between the core and the user interface.
///
library;

/// Interface providing user interactions to the core.
///
/// This is the general, application-wide access point for user interactions. Domain specific
/// operations are separated into more specialized sub-interfaces.
abstract interface class PresentationBoundary {
  /// Initializes the user interface.
  ///
  /// This may display some kind of "loading" or "splash" screen if appropriate.
  void initUserInterface();

  /// Change the active domain to the *Route Database* domain.
  void switchToRouteDb();

  /// Change the active domain to the *Journal* domain.
  void switchToJournal();

  /// Change the active domain to the *Knowledgebase* domain.
  void switchToKnowledgebase();

  /// Change the active domain to the *About* domain.
  void switchToAbout();
}
