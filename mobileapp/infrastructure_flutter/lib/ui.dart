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

  @override
  void initializeUserInterface(
    String appName,
    String splashString,
    DomainLabelDefinition routeLabels,
  ) {
    runApp(
      MainWidget(
        appName,
        splashString,
        routeLabels,
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
  void switchToRouteDb() {
    _switchToRoute(UiRoute.routedb.toRouteString());
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
  void switchToAbout() {
    _switchToRoute(UiRoute.about.toRouteString());
  }

  /// Let the UI display the page with the given [routeString], forwarding the providing
  /// [routeArguments] (if any).
  void _switchToRoute(String routeString, {Object? routeArguments}) {
    // Directly switch to the requested route if the UI is already initialized (=normal case),
    // but delay it if it is not (i.e. before the initial page is shown).
    if (!_uiState.isInitializing()) {
      unawaited(_uiState
          .getNavigatorKey()
          .currentState!
          .pushNamed(routeString, arguments: routeArguments));
    } else {
      SchedulerBinding.instance.addPostFrameCallback((_) {
        unawaited(_uiState
            .getNavigatorKey()
            .currentState!
            .pushNamed(routeString, arguments: routeArguments));
      });
    }
  }
}
