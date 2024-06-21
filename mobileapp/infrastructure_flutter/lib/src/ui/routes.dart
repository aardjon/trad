///
/// Definition of the available Flutter routes.
///
library;

/// Identifier of a single route within the GUI.
/// This is used to e.g. map label strings to routes and to avoid hard coded route "URIs".
enum UiRoute {
  /// Route to the splash screen.
  ///
  /// This should never be switched to, it is meant to be used once during startup only.
  splash,

  /// Route to the *Journal* main screen.
  journal,

  /// Route to the *Route Database* main screen.
  routedb,

  /// Route to the *Knowledgebase* main screen.
  knowledgebase,

  /// Route to the *About* screen.
  about;

  /// Returns the concrete Flutter route/path string that corresponds to this item.
  ///
  /// Route strings look similar to a path and always refer to a single Flutter page/screen. They
  /// are used for navigating between pages.
  String toRouteString() {
    switch (this) {
      case splash:
        return '/splash';
      case journal:
        return '/journal';
      case routedb:
        return '/routedb';
      case knowledgebase:
        return '/knowledgebase';
      case about:
        return '/about';
    }
  }
}
