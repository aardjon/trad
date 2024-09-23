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

  /// Route to the *summit list* screen (one of the *route database* screens).
  summitlist,

  /// Route to the *summit details* screen (one of the *route database* screens) showing e.g. the
  /// list of climbing routes to a certain summit.
  summitdetails,

  /// Route to the *route details* screen (one of the *route database* screens) showing e.g. the
  /// community comments of a certain route.
  routedetails,

  /// Route to the *Knowledgebase* main screen.
  knowledgebase,

  /// Route to the *Settings* screen.
  settings;

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
      case summitlist:
        return '/routedb/summits';
      case summitdetails:
        return '/routedb/summit';
      case routedetails:
        return '/routedb/route';
      case knowledgebase:
        return '/knowledgebase';
      case settings:
        return '/settings';
    }
  }
}
