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
  /// This is the only real instance of the state, all other clients should only reference this one
  /// and never create their own!
  static final GuiState _uiState = GuiState();

  /// The central summit list state of the UI.
  ///
  /// This is the only real instance of this, all other clients should only reference this one
  /// and never create their own!
  // TODO(aardjon): There should be no central state within the GUI implementation, i.e. each summit
  //    list widget should probably have its own notifier/state (the UI interface documentation is
  //    correct, the current implementation is not). Can we find a better solution for this?
  static final SummitListNotifier _summitListState = SummitListNotifier();

  static final RouteListNotifier _routeListState = RouteListNotifier();

  static final PostListNotifier _postListState = PostListNotifier();

  @override
  void initializeUserInterface(
    String appName,
    String splashString,
    MainMenuModel menuModel,
  ) {
    runApp(
      MainWidget(
        appName,
        splashString,
        menuModel,
        ApplicationWideController(),
        _uiState,
        _summitListState,
        _routeListState,
        _postListState,
      ),
    );
    // Set the UI state to initialized after the first event frame is done.
    SchedulerBinding.instance.addPostFrameCallback((_) {
      _uiState.setInitialized();
    });
  }

  @override
  void showSummitList(SummitListModel model) {
    _logger.debug('Displaying summit list page');
    _switchToRoute(UiRoute.summitlist.toRouteString(), routeArguments: model);
  }

  @override
  void updateSummitList(List<ListViewItem> summitItems) {
    _summitListState.replaceSummits(summitItems);
  }

  @override
  void showSummitDetails(SummitDetailsModel model) {
    _logger.debug('Displaying route list page');
    _switchToRoute(UiRoute.summitdetails.toRouteString(), routeArguments: model);
  }

  @override
  void updateRouteList(List<ListViewItem> routeItems, List<ListViewItem> sortMenuItems) {
    _logger.debug('Updating route list data');
    _routeListState.replaceRoutes(routeItems, sortMenuItems);
  }

  @override
  void showRouteDetails(RouteDetailsModel model) {
    _logger.debug('Displaying post list page');
    _switchToRoute(UiRoute.routedetails.toRouteString(), routeArguments: model);
  }

  @override
  void updatePostList(List<ListViewItem> postItems, List<ListViewItem> sortMenuItems) {
    _logger.debug('Updating post list data');
    _postListState.replacePosts(postItems, sortMenuItems);
  }

  @override
  void switchToJournal() {
    _switchToRoute(UiRoute.journal.toRouteString());
  }

  @override
  void showKnowledgebase(KnowledgebaseModel document) {
    _logger.debug("Displaying knowledgebase page with title '${document.documentTitle}'");
    _switchToRoute(UiRoute.knowledgebase.toRouteString(), routeArguments: document);
  }

  @override
  void switchToSettings() {
    _switchToRoute(UiRoute.settings.toRouteString());
  }

  /// Let the UI display the page with the given [routeString], forwarding the providing
  /// [routeArguments] (if any).
  void _switchToRoute(String routeString, {Object? routeArguments}) {
    // Directly switch to the requested route if the UI is already initialized (=normal case),
    // but delay it if it is not (i.e. before the initial page is shown).
    if (!_uiState.isInitializing()) {
      unawaited(
        _uiState.getNavigatorKey().currentState!.pushNamed(routeString, arguments: routeArguments),
      );
    } else {
      SchedulerBinding.instance.addPostFrameCallback((_) {
        unawaited(
          _uiState
              .getNavigatorKey()
              .currentState!
              .pushNamed(routeString, arguments: routeArguments),
        );
      });
    }
  }
}
