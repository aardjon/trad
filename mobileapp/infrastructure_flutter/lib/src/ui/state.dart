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

  /// The central route db state of the UI.
  ///
  /// This is the only real instance of this, all other clients (views) should only reference this
  /// one and never create their own!
  final RouteDbStatusNotifier routeDBState = RouteDbStatusNotifier();

  /// All summit list notifiers for all alive summit list widgets assigned to a certain context.
  ///
  /// The Notifier instances can be retrieved with [getSummitListNotifier()] and deleted with
  /// [resetNotifiers()].
  ///
  /// Map key is a string containing the "parent" summit ID.
  final Map<String, DeferableOptionalDataListNotifier> _summitLists =
      <String, DeferableOptionalDataListNotifier>{};

  /// All summit list notifiers for all alive route list widgets assigned to a certain context.
  ///
  /// The Notifier instances can be retrieved with [getSummitListNotifier()] and deleted with
  /// [resetNotifiers()].
  ///
  /// Map key is a string containing the "parent" summit ID.
  final Map<String, DeferableOptionalDataListNotifier> _routeLists =
      <String, DeferableOptionalDataListNotifier>{};

  /// Returns the Notifier providing nearby summits for the given [contextItemId].
  ///
  /// If there is none for this context yet, a new one will be created.
  DeferableOptionalDataListNotifier getSummitListNotifier(ItemDataId? contextItemId) {
    String idStr = contextItemId == null ? '' : '$contextItemId';
    String mapKey = '/$idStr';
    DeferableOptionalDataListNotifier? state = _summitLists[mapKey];
    if (state == null) {
      state = DeferableOptionalDataListNotifier();
      _summitLists[mapKey] = state;
    }
    return state;
  }

  /// Returns the Notifier providing route or the given [contextItemId].
  ///
  /// If there is none for this context yet, a new one will be created.
  DeferableOptionalDataListNotifier getRouteListNotifier(ItemDataId? contextItemId) {
    String idStr = contextItemId == null ? '' : '$contextItemId';
    String mapKey = '/$idStr';
    DeferableOptionalDataListNotifier? state = _routeLists[mapKey];
    if (state == null) {
      state = DeferableOptionalDataListNotifier();
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
  final DeferableOptionalDataListNotifier summitListState = DeferableOptionalDataListNotifier();

  /// The central post list state of the UI.
  ///
  /// This is the only real instance of this, all other clients (views) should only reference this
  /// one and never create their own!
  final PostListNotifier postListState = PostListNotifier();
}

enum _RouteDbStatus {
  /// No route database is available.
  missing,

  /// The route database is currently being updated in the background (and therefore not available).
  updating,

  /// A route database if available and loaded and thus can be used normally.
  activated,
}

/// Represents the current state of the route database and notifies about changes.
class RouteDbStatusNotifier extends ChangeNotifier {
  /// The current status of the route database.
  _RouteDbStatus _routeDbStatus = _RouteDbStatus.missing;

  /// A message informing the user about the current state of the route database domain, e.g. when
  /// it's not available because of missing data. Set to `null` if no such message should be shown
  /// at all.
  String? _routeDbStatusMessage;

  /// A message informaing the user about the last error that occured during a DB update. Set to
  /// `null` if no such message shall be displayed.
  String? _lastUpdateErrorMessage;

  /// The identifier of the currently used route database. Only set if [_routeDbStatus] is
  /// [_RouteDbStatus.activated].
  String _routeDbIdentifier = '';

  /// The attribution data of the currently loaded route database. Only set if [_routeDbStatus] is
  /// [_RouteDbStatus.activated].
  List<ListViewItem> _dataSourceAttributions = <ListViewItem>[];

  /// Returns true if the route database is currently available, false if not.
  bool isRouteDbAavailable() {
    return _routeDbStatus == _RouteDbStatus.activated;
  }

  /// Returns the identifying label of the current route database.
  String getRouteDbIdentifier() {
    return _routeDbIdentifier;
  }

  /// Returns the data source attribution information for the current route database. Returns an
  /// empty list if no route database is available.
  List<ListViewItem> getDataSourceAttributions() {
    return _dataSourceAttributions;
  }

  /// Returns the additional message about the route database that should be displayed to the user.
  ///
  /// If there is no such additional message, `null` is returned.
  String? getRouteDbAvailabilityMessage() {
    return _routeDbStatusMessage;
  }

  /// Returns true if the route database is currently being updated, or false if not.
  bool isRouteDbUpdateInProgress() {
    return _routeDbStatus == _RouteDbStatus.updating;
  }

  /// Returns the last DB update error message that should be displayed to the user. If there is no
  /// such additional message, `null` is returned.
  ///
  /// Note: The message is discarded afterwards, meaning that it can be obtained from the Notifier
  /// only once.
  String? popLastUpdateErrorMessage() {
    String? message = _lastUpdateErrorMessage;
    _lastUpdateErrorMessage = null;
    return message;
  }

  /// Stores the given [message] to be displayed as DB update error with the next view update.
  ///
  /// This is not a simple 'setter' to avoid the impression that the get/set operations on this
  /// member work as usual. That's also why the linter warning is ignored here.
  // ignore: use_setters_to_change_properties
  void setLastUpdateErrorMessage(String message) {
    _lastUpdateErrorMessage = message;
  }

  /// Changes the displayed database status to `activated`, using the given [dbIdentifier] and
  /// [dataSourceAttributions]. All listeners are notified so that that e.g. views can be updated.
  void setStatusActivated({
    required String dbIdentifier,
    required List<ListViewItem> dataSourceAttributions,
  }) {
    _routeDbStatus = _RouteDbStatus.activated;
    _routeDbStatusMessage = null;
    _routeDbIdentifier = dbIdentifier;
    _dataSourceAttributions = dataSourceAttributions;
    notifyListeners();
  }

  /// Changes the displayed database status to `missing` and displays the given [label] and
  /// [userHint]. All listeners are notified so that that e.g. views can be updated.
  void setStatusMissing(String label, String userHint) {
    _routeDbStatus = _RouteDbStatus.missing;
    _routeDbStatusMessage = userHint;
    _routeDbIdentifier = label;
    _dataSourceAttributions = <ListViewItem>[];
    notifyListeners();
  }

  /// Changes the displayed database status to `updating`. All listeners are notified so that that
  /// e.g. views can be updated.
  void setStatusUpdating() {
    _routeDbStatus = _RouteDbStatus.updating;
    notifyListeners();
  }
}

/// Notifier mixin that knows whether any data is available at all (or not), no matter of what the
/// actual data is like. Data may be missing e.g. due to an error or some unmet precondition, or
/// there may just be no data to display at all.
mixin FallbackMessageNotifier on ChangeNotifier {
  ///
  late String? _message;

  /// Return true if the regular data is available for display, or false if not. Must be
  /// implemented by the using model classes. If [canDisplayData] returns false, a
  /// [fallbackMessage] MUST have been set!
  bool canDisplayData();

  /// Return an explanatory message that can be shown to the user. The message shall provide
  /// details about the problem together with information about its consequences and what the user
  /// can do about.
  String get fallbackMessage => _message!;

  /// Define the message text to be displayed to the user instead of the actual data.
  set fallbackMessage(String message) => _message = message;
}

/// Notifier mixin that knows whether the data is still being loaded or already available.
mixin DeferableDataNotifier on ChangeNotifier {
  /// True while the data is still loading, false if it is available.
  bool _isLoading = true;

  /// Return true while data is already loaded and should be available, otherweise false.
  bool get dataLoaded => !_isLoading;

  /// Set to true after the data has been loaded and can be displayed.
  set dataLoaded(bool loadingComplete) => _isLoading = !loadingComplete;
}

/// Notifier providing data structured as a list.
class DataListNotifier extends ChangeNotifier {
  /// The current data.
  List<ListViewItem> _data = <ListViewItem>[];

  /// The currently available context action items.
  List<ListViewItem> _actionItems = <ListViewItem>[];

  /// Returns the total number of data items that shall currently be displayed.
  int getDataItemCount() {
    return _data.length;
  }

  /// Returns the data item with the requested list [index].
  ///
  /// The [index] is zero based and must be smaller than the value returned by [getDataItemCount].
  /// For invalid indexes, an Exception is raised.
  ListViewItem getDataItem(int index) {
    return _data[index];
  }

  /// Returns the action items for the current dats.
  List<ListViewItem> getActionItems() {
    return _actionItems;
  }

  /// Replaces the current data and action items with the new ones defined by [data] and [actions].
  ///
  /// All listeners are notified so that e.g. views can be updated.
  void replaceData(
    List<ListViewItem> data,
    List<ListViewItem> actions,
  ) {
    _data = data;
    _actionItems = actions;
    notifyListeners();
  }
}

/// Represents the current data state of a list that may be empty.
class OptionalDataListNotifier extends DataListNotifier with FallbackMessageNotifier {
  @override
  bool canDisplayData() {
    return _data.isNotEmpty;
  }
}

/// Represents the current data state of a list that may be empty, and may need some time to load.
class DeferableOptionalDataListNotifier extends OptionalDataListNotifier
    with DeferableDataNotifier {
  @override
  void replaceData(List<ListViewItem> data, List<ListViewItem> actions) {
    super.dataLoaded = true;
    super.replaceData(data, actions);
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
