///
/// Definition of the boundary between UI adapters (`adapters` ring) and a concrete UI
/// implementation (`infrastructure` ring).
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

  /// Constructor for directly initializing all members.
  const DomainLabelDefinition(
    this.journalLabel,
    this.routedbLabel,
    this.knowledgebaseLabel,
    this.aboutLabel,
  );
}

/// Model that provides all data needed to display a single knowledge base document to the UI.
class KnowledgebaseModel {
  /// Title of the document being displayed.
  final String documentTitle;

  /// Markdown content of the document being displayed.
  final String documentContent;

  /// Constructor for directly initializing all members.
  KnowledgebaseModel(this.documentTitle, this.documentContent);
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

  /// Request the UI to display the provided [document] on the  *Knowledge Base* screen.
  void showKnowledgebase(KnowledgebaseModel document);

  /// Request the UI to display the *About* screen.
  void switchToAbout();
}
