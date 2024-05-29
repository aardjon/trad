///
/// Definition of application-wide presenters that are not bound to a certain domain.
///
/// Presenters connect the `core` to the concrete UI implementation (in this direction) and are
/// responsible for providing displayable data (i.e. "everything the user can see").
///
/// In a way, Presenters are the counterpart of Controllers.
///
library;

import 'package:core/boundaries/presentation.dart';
import 'package:core/entities/knowledgebase.dart';
import 'package:crosscuttings/di.dart';

import '../boundaries/ui.dart';

/// Implementation of the presentation boundary used by the core to interact with the user.
class ApplicationWidePresenter implements PresentationBoundary {
  /// DI instance for obtaining dependencies from other rings.
  final DependencyProvider _dependencyProvider = DependencyProvider();

  @override
  void initUserInterface() {
    ApplicationUiBoundary ui =
        _dependencyProvider.provide<ApplicationUiBoundary>();
    ui.initializeUserInterface(
      'trad - Climbing in Saxony',
      'Initializing...',
      const DomainLabelDefinition(
        "Journal",
        "Climbing Routes",
        "Knowledgebase",
        "About",
      ),
    );
  }

  @override
  void switchToRouteDb() {
    ApplicationUiBoundary ui =
        _dependencyProvider.provide<ApplicationUiBoundary>();
    ui.switchToRouteDb();
  }

  @override
  void switchToJournal() {
    ApplicationUiBoundary ui =
        _dependencyProvider.provide<ApplicationUiBoundary>();
    ui.switchToJournal();
  }

  @override
  void showKnowledgebaseDocument(KnowledgebaseDocument document) {
    KnowledgebaseModel kbPageModel = KnowledgebaseModel(document.title, document.content);
    ApplicationUiBoundary ui = _dependencyProvider.provide<ApplicationUiBoundary>();
    ui.showKnowledgebase(kbPageModel);
  }

  @override
  void switchToAbout() {
    ApplicationUiBoundary ui =
        _dependencyProvider.provide<ApplicationUiBoundary>();
    ui.switchToAbout();
  }
}
