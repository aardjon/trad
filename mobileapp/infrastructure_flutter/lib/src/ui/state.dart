///
/// Contains the central UI state.
///
library;

import 'package:flutter/material.dart';

import 'package:adapters/boundaries/ui.dart';

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

  /// The central settings state of the UI.
  ///
  /// This is the only real instance of this, all other clients (views) should only reference this
  /// one and never create their own!
  final SettingsNotifier settingsState = SettingsNotifier();

  /// All summit list notifiers for all alive summit list widgets assigned to a certain context.
  ///
  /// The Notifier instances can be retrieved with [getSummitListNotifier()] and deleted with
  /// [resetNotifiers()].
  ///
  /// Map key is a string containing the "parent" summit ID.
  final Map<String, SummitListNotifier> _summitLists = <String, SummitListNotifier>{};

  /// All summit list notifiers for all alive route list widgets assigned to a certain context.
  ///
  /// The Notifier instances can be retrieved with [getSummitListNotifier()] and deleted with
  /// [resetNotifiers()].
  ///
  /// Map key is a string containing the "parent" summit ID.
  final Map<String, RouteListNotifier> _routeLists = <String, RouteListNotifier>{};

  /// Returns the Notifier providing nearby summits for the given [contextItemId].
  ///
  /// If there is none for this context yet, a new one will be created.
  SummitListNotifier getSummitListNotifier(ItemDataId? contextItemId) {
    String idStr = contextItemId == null ? '' : '$contextItemId';
    String mapKey = '/$idStr';
    SummitListNotifier? state = _summitLists[mapKey];
    if (state == null) {
      state = SummitListNotifier();
      _summitLists[mapKey] = state;
    }
    return state;
  }

  /// Returns the Notifier providing route or the given [contextItemId].
  ///
  /// If there is none for this context yet, a new one will be created.
  RouteListNotifier getRouteListNotifier(ItemDataId? contextItemId) {
    String idStr = contextItemId == null ? '' : '$contextItemId';
    String mapKey = '/$idStr';
    RouteListNotifier? state = _routeLists[mapKey];
    if (state == null) {
      state = RouteListNotifier();
      _routeLists[mapKey] = state;
    }
    return state;
  }

  /// Removes all context sensitive notifiers.
  /// Must be called when discarding previous widgets to avoid memory leaks.
  void resetNotifiers() {
    _summitLists.clear();
    _routeLists.clear();
  }

  /// The central summit list state of the UI.
  ///
  /// This is the only real instance of this, all other clients (views) should only reference this
  /// one and never create their own!
  final SummitListNotifier summitListState = SummitListNotifier();

  /// The central post list state of the UI.
  ///
  /// This is the only real instance of this, all other clients (views) should only reference this
  /// one and never create their own!
  final PostListNotifier postListState = PostListNotifier();
}

/// Represents the current state of the application settings and notifies about changes.
class SettingsNotifier extends ChangeNotifier {
  /// The activation status of the route database: true (available) or false (unavailable).
  bool _routeDbActivationStatus = true;

  /// A message informing the user about the current state of the route database domain, e.g. when
  /// it's not available because of missing data. Set to `null` if no such message should be shown
  /// at all.
  String? _routeDbAvailabilityMessage;

  /// The identifier of the currently used route database
  String _routeDbIdentifier = '';

  List<ListViewItem> _dataSourceAttributions = <ListViewItem>[];

  /// Displays whether the route db is currently being updated in the background (true) or not
  /// (false).
  bool _routeDbUpdateInProgress = false;

  /// Returns true if the route database is currently available, false if not.
  bool isRouteDbAavailable() {
    return _routeDbActivationStatus;
  }

  /// Returns the identifying label of the current route database.
  String getRouteDbIdentifier() {
    return _routeDbIdentifier;
  }

  /// Returns the data source attribution information for the current route database.
  List<ListViewItem> getDataSourceAttributions() {
    return _dataSourceAttributions;
  }

  /// Returns the additional message about the route database that should be displayed to the user.
  ///
  /// If there is no such additional message, `null` is returned.
  String? getRouteDbAvailabilityMessage() {
    return _routeDbAvailabilityMessage;
  }

  /// Returns true if the route database is currently being updated, or false if not.
  bool isRouteDbUpdateInProgress() {
    return _routeDbUpdateInProgress;
  }

  /// Replaces the status information of the route database with the given [dbIdentifier] and
  /// [availabilityMessage].
  ///
  /// All listeners are notified so that that e.g. views can be updated.
  void updateRouteDbStatus({
    required bool routeDbActivationStatus,
    required String dbIdentifier,
    required List<ListViewItem> dataSourceAttributions,
    String? availabilityMessage,
  }) {
    _routeDbActivationStatus = routeDbActivationStatus;
    _routeDbAvailabilityMessage = availabilityMessage;
    _routeDbIdentifier = dbIdentifier;
    _dataSourceAttributions = dataSourceAttributions;
    notifyListeners();
  }

  /// Updates the progress status of a currently running route DB update task to [inProgress]:
  /// true if the task is running, false if not.
  void updateRouteDbUpdateProgress({required bool inProgress}) {
    _routeDbUpdateInProgress = inProgress;
    notifyListeners();
  }
}

/// Notifier that knows whether the data is available at all (or not), no matter of what the actual
/// data is like. Data may be missing e.g. due to an error or some unmet precondition, or there may
/// just be no data to display at all.
mixin AlternateStatusMessageNotifier on ChangeNotifier {
  ///
  String? _message;

  /// Return true if the regular data is available for display, or false if not.
  bool canDisplayData() {
    return _message == null;
  }

  /// Return an explanatory message that can be shown to the user. The message shall provide
  /// details about the problem together with information about its consequences and what the user
  /// can do about.
  ///
  /// Must only be called when [canDisplayData] returnes false!
  String getAlternateMessage() {
    return _message!;
  }

  /// Define the message text to be displayed to the user instead of the actual data widget.
  /// All listeners are notified so that that e.g. views can be updated.
  void setAlternateMessage(String message) {
    _message = message;
    notifyListeners();
  }
}

/// Represents the current state of the summit list and notifies about changes.
class SummitListNotifier extends ChangeNotifier with AlternateStatusMessageNotifier {
  /// The current list of summits.
  List<ListViewItem> _summits = <ListViewItem>[];

  /// The currently available context action items.
  List<ListViewItem> _contextActionItems = <ListViewItem>[];

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

  /// Returns the action items for the current summit list.
  List<ListViewItem> getContextActionItems() {
    return _contextActionItems;
  }

  /// Replaces the current summit list with the new one defined by [summits].
  ///
  /// All listeners are notified so that that e.g. views can be updated.
  void replaceSummits(
    List<ListViewItem> summits,
    List<ListViewItem> contextActionItems,
  ) {
    _summits = summits;
    _contextActionItems = contextActionItems;
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
