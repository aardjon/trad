///
/// Contains the central UI state.
///
library;

import 'package:adapters/boundaries/ui.dart';
import 'package:flutter/material.dart';

/// The central GUI state.
///
/// This class contains all information that represent the current state of the GUI. Note that,
/// while the GUI doesn't explicitly show any state to the outside, it of course has some internal
/// state that must be kept centrally. But as this is still a UI internal implementation, it does
/// not store any kind of application/business state.
///
/// There should ever be only one instance of this class.
class GuiState {
  /// State flag storing whether the UI is currently initializing (true) or not (false).
  bool _isInitializing = true;

  /// The global navigation key instance.
  static final GlobalKey<NavigatorState> _navigatorKey = GlobalKey<NavigatorState>();

  /// Defines whether the GUI is currently initializing.
  ///
  /// While the UI is initializing, direct repaint is not possible. In this case, a repaint request
  /// must be delayed to the end of the current event frame. After initialization (i.e. after the
  /// app enters the central event loop), all repaints can be scheduled directly for better
  /// performance and to avoid race conditions between direct and delayed executions. Furthermore,
  /// all other state members may be empty/invalid during initialization.
  /// This flag is only set to false exactly once and then stays in this state forever.
  bool isInitializing() {
    return _isInitializing;
  }

  /// Changes the UI state to be initialized.
  void setInitialized() {
    _isInitializing = false;
  }

  /// Returns the global navigation key used for switching between pages.
  ///
  /// This key is needed for switching without having a `context` object.
  GlobalKey<NavigatorState> getNavigatorKey() {
    return _navigatorKey;
  }
}

/// Represents the current state of the summit list and notifies about changes.
class SummitListNotifier extends ChangeNotifier {
  /// The current list of summits.
  List<ListViewItem> _summits = <ListViewItem>[];

  /// Returns the total number of summits that shall currently be displayed.
  int getSummitCount() {
    return _summits.length;
  }

  /// Returns the summit with the requested list [index].
  ///
  /// The [index] is zero based and must be smaller than the value returned by [getSummitCount].
  /// For invalid indexes, an Exception is raised.
  ListViewItem getSummitItem(int index) {
    return _summits[index];
  }

  /// Replaces the current summit list with the new one defined by [summits].
  ///
  /// All listeners are notified so that that e.g. views can be updated.
  void replaceSummits(List<ListViewItem> summits) {
    _summits = summits;
    notifyListeners();
  }
}

/// Represents the current state of the route list and notifies about changes.
class RouteListNotifier extends ChangeNotifier {
  /// The current list of routes.
  List<ListViewItem>? _routes;

  /// The items of the sort menu to be displayed for the current route list (may e.g. emphasize the
  /// used sort criterion).
  List<ListViewItem>? _sortMenuItems;

  /// Returns true if some route data is available for display.
  ///
  /// Route data must be provided via [replaceRoutes]. Without route data, most of the other methods
  /// will fail.
  bool routesLoaded() {
    return _routes != null && _sortMenuItems != null;
  }

  /// Returns the total number of routes that shall currently be displayed.
  ///
  /// Throws an exception if there is no route data (i.e. if [routesLoaded] returns false).
  int getRouteCount() {
    return _routes!.length;
  }

  /// Returns the route list item with the requested list index.
  ///
  /// The [index] is zero based and must be smaller than the value returned by [getRouteCount].
  /// For invalid indexes, an Exception is raised. If there is no route data (i.e. if [routesLoaded]
  /// returns false), an Exception is raised.
  ListViewItem getRouteItem(int index) {
    return _routes![index];
  }

  /// Returns the sort menu items for the current route list.
  ///
  /// Throws an exception if there is no route data (i.e. if [routesLoaded] returns false).
  List<ListViewItem> getSortMenuItems() {
    return _sortMenuItems!;
  }

  /// Replaces the current route list with the new one defined by [routes].
  ///
  /// All listeners are notified so that that e.g. views can be updated.
  void replaceRoutes(List<ListViewItem> routes, List<ListViewItem> sortMenuItems) {
    _routes = routes;
    _sortMenuItems = sortMenuItems;
    notifyListeners();
  }
}

/// Represents the current state of the post list and notifies about changes.
class PostListNotifier extends ChangeNotifier {
  /// The current list of posts.
  List<ListViewItem>? _posts;

  /// The items of the sort menu to be displayed for the current route list (may e.g. emphasize the
  /// used sort criterion).
  List<ListViewItem>? _sortMenuItems;

  /// Returns true if some post data is available for display.
  ///
  /// Post data must be provided via [replacePosts]. Without post data, most of the other methods
  /// will fail.
  bool postsLoaded() {
    return _posts != null && _sortMenuItems != null;
  }

  /// Returns the total number of posts that shall currently be displayed.
  ///
  /// Throws an exception if there is no route data (i.e. if [postsLoaded] returns false).
  int getPostCount() {
    return _posts!.length;
  }

  /// Returns the post with the requested list [index].
  ///
  /// The [index] is zero based and must be smaller than the value returned by [getPostCount].
  /// For invalid indexes, an Exception is raised. If there is no route data (i.e. if [postsLoaded]
  /// returns false), an Exception is raised.
  ListViewItem getPostItem(int index) {
    return _posts![index];
  }

  /// Returns the sort menu items for the current post list.
  ///
  /// Throws an exception if there is no post data (i.e. if [postsLoaded] returns false).
  List<ListViewItem> getSortMenuItems() {
    return _sortMenuItems!;
  }

  /// Replaces the current post list with the new one defined by [posts].
  ///
  /// All listeners are notified so that that e.g. views can be updated.
  void replacePosts(List<ListViewItem> posts, List<ListViewItem> sortMenuItems) {
    _posts = posts;
    _sortMenuItems = sortMenuItems;
    notifyListeners();
  }
}
