///
/// Definition of the boundary between UI adapters and a concrete UI implementation.
///
library;

/// Definition of a label string for each application domain.
///
/// These labels are display strings and should describe the domain very shortly. They can be used
/// in the title bar or application menu, for example.
class DomainLabelDefinition {
  /// Label for the journal domain.
  final String journalLabel;

  /// Label for the route db domain.
  final String routedbLabel;

  /// Label for the knowledgebase domain.
  final String knowledgebaseLabel;

  /// Label for the about domain.
  final String aboutLabel;

  const DomainLabelDefinition(
    this.journalLabel,
    this.routedbLabel,
    this.knowledgebaseLabel,
    this.aboutLabel,
  );
}

/// Boundary interface to the concrete, domain-independent part of the UI implementation.
///
/// This interface provides general, application-wide UI operations. Domain specific concerns are
/// separated into more specialized sub-interfaces.
abstract interface class ApplicationUiBoundary {
  /// Initializes the user interface for the application with the display name [appName].
  ///
  /// The provided [appName] can be displayed e.g. in some title or header bar, the [splashString]
  /// is displayed during the startup phase before the UI is ready to for user interactions. The
  /// [routeLabels] are used e.g. for the main navigation menu.
  void initializeUserInterface(
    String appName,
    String splashString,
    DomainLabelDefinition routeLabels,
  );

  /// Request the UI to display the *Route Database* screen.
  void switchToRouteDb();

  /// Request the UI to display the *Journal* screen.
  void switchToJournal();

  /// Request the UI to display the *Knowledgebase* screen.
  void switchToKnowledgebase();

  /// Request the UI to display the *About* screen.
  void switchToAbout();
}
