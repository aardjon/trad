///
/// Flutter implementation of trad's user interface.
///
/// This library is responsible for all UI look & feel, but must neither contain any business logic
/// nor any display strings. Concrete UI implementations shall be as dumb as possible!
///
library;

import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter/scheduler.dart';

import 'package:adapters/boundaries/ui.dart';
import 'package:adapters/controllers.dart';
import 'package:crosscuttings/logging/logger.dart';

import 'src/ui/framing.dart';
import 'src/ui/routes.dart';
import 'src/ui/state.dart';

/// Logger to be used in this library file.
final Logger _logger = Logger('trad.infrastructure_flutter.ui');

/// Implementation of the boundary interface used by the `adapters` to communicate with the concrete
/// UI.
///
/// This is basically an adapter which delegates all calls to the corresponding Flutter/widget
/// operation.
class ApplicationUI implements ApplicationUiBoundary {
  /// The central state of the UI.
  ///
  /// This is the only real instance of the state, all other clients (views) should only reference
  /// this one and never create their own!
  static final GuiState _uiState = GuiState();

  @override
  void initializeUserInterface(String appName, String splashString, MainMenuModel menuModel) {
    runApp(
      MainWidget(
        appName,
        splashString,
        menuModel,
        ApplicationWideController(),
        _uiState,
      ),
    );
    // Set the UI state to initialized after the first event frame is done.
    SchedulerBinding.instance.addPostFrameCallback((_) {
      _uiState.setInitialized();
    });
  }

  @override
  void setStatusActivated({
    required String label,
    required List<ListViewItem> dataSourceAttributions,
  }) {
    _uiState.routeDBState.setStatusActivated(
      dbIdentifier: label,
      dataSourceAttributions: dataSourceAttributions,
    );
  }

  @override
  void setStatusMissing({required String label, required String userHint}) {
    _uiState.routeDBState.setStatusMissing(label, userHint);
  }

  @override
  void setStatusUpdating() {
    _uiState.routeDBState.setStatusUpdating();
  }

  @override
  void showRouteDbUpdateErrorMessage(String message) {
    _uiState.routeDBState.setLastUpdateErrorMessage(message);
  }

  @override
  void showSummitList(SummitListModel model) {
    _logger.debug('Displaying summit list page');
    _uiState.resetNotifiers();
    _switchToRoute(UiRoute.summitlist.toRouteString(), isRoot: true, routeArguments: model);
  }

  @override
  void updateSummitList(List<ListViewItem> summitItems) {
    _uiState.summitListState.replaceSummits(summitItems, <ListViewItem>[]);
  }

  @override
  void showSummitDetails(SummitDetailsModel model) {
    _logger.debug('Displaying summit details page');
    _switchToRoute(UiRoute.summitdetails.toRouteString(), isRoot: false, routeArguments: model);
  }

  @override
  void updateRouteList(
    ItemDataId contextItemId,
    List<ListViewItem> routeItems,
    List<ListViewItem> sortMenuItems,
  ) {
    _logger.debug('Updating route list data');
    _uiState.getRouteListNotifier(contextItemId).replaceRoutes(routeItems, sortMenuItems);
  }

  @override
  void updateContextualSummitList(
    ItemDataId contextItemId,
    List<ListViewItem> summitItems,
    List<ListViewItem> contextActionItems,
  ) {
    _logger.debug('Updating contextual summit list data');
    _uiState.getSummitListNotifier(contextItemId).replaceSummits(summitItems, contextActionItems);
  }

  @override
  void showRouteDetails(RouteDetailsModel model) {
    _logger.debug('Displaying post list page');
    _switchToRoute(UiRoute.routedetails.toRouteString(), isRoot: false, routeArguments: model);
  }

  @override
  void updatePostList(List<ListViewItem> postItems, List<ListViewItem> sortMenuItems) {
    _logger.debug('Updating post list data');
    _uiState.postListState.replacePosts(postItems, sortMenuItems);
  }

  @override
  void switchToJournal() {
    _uiState.resetNotifiers();
    _switchToRoute(
      UiRoute.journal.toRouteString(),
      isRoot: true,
    );
  }

  @override
  void showKnowledgebase(KnowledgebaseModel document) {
    _logger.debug("Displaying knowledgebase page with title '${document.documentTitle}'");
    _uiState.resetNotifiers();
    _switchToRoute(UiRoute.knowledgebase.toRouteString(), isRoot: true, routeArguments: document);
  }

  @override
  void showSettings(SettingsModel model) {
    _logger.debug('Displaying settings page');
    _uiState.resetNotifiers();
    _switchToRoute(UiRoute.settings.toRouteString(), isRoot: true, routeArguments: model);
  }

  @override
  void showAppInfo(AppInfoModel model) {
    _logger.debug('Displaying app info page');
    _uiState.resetNotifiers();
    _switchToRoute(UiRoute.appinfo.toRouteString(), isRoot: true, routeArguments: model);
  }

  /// Let the UI display the page with the given [routeString], forwarding the providing
  /// [routeArguments] (if any). If [isRoot] is set to false, the new route is added to the route
  /// stack as usual (and thus the user can go back to the previous one). If it is true, the whole
  /// previous page stack is cleared (so that the user cannot go back).
  void _switchToRoute(String routeString, {required bool isRoot, Object? routeArguments}) {
    // Directly switch to the requested route if the UI is already initialized (=normal case),
    // but delay it if it is not (i.e. before the initial page is shown).
    if (!_uiState.isInitializing()) {
      NavigatorState state = _uiState.getNavigatorKey().currentState!;
      if (isRoot) {
        unawaited(
          state.pushNamedAndRemoveUntil(
            routeString,
            (Route<dynamic> route) => false,
            arguments: routeArguments,
          ),
        );
      } else {
        unawaited(
          state.pushNamed(
            routeString,
            arguments: routeArguments,
          ),
        );
      }
    } else {
      SchedulerBinding.instance.addPostFrameCallback((_) {
        NavigatorState state = _uiState.getNavigatorKey().currentState!;
        unawaited(
          state.pushReplacementNamed(
            routeString,
            arguments: routeArguments,
          ),
        );
      });
    }
  }
}
