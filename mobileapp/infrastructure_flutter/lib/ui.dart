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

/// Logger to be used in this library file.
final Logger _logger = Logger('trad.infrastructure_flutter.ui');

/// Implementation of the boundary interface used by the `adapters` to communicate with the concrete
/// UI.
///
/// This is basically an adapter which delegates all calls to the corresponding Flutter/widget
/// operation.
class ApplicationUI implements ApplicationUiBoundary {
  /// Global state of the UI.
  /// While the UI is initializing, direct repaint is not possible. In this case, a repaint request
  /// must be delayed to the end of the current event frame. After initialization (i.e. after the
  /// app enters the central event loop), all repaints are scheduled directly for better performance
  /// and to avoid race conditions between direct and delayed executions.
  /// This flag is only set to true exactly once and then stays in this state forever.
  static bool _uiIsInitializing = true;

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
      ),
    );
    // Set the global set to isInitialized after the first event frame is done.
    SchedulerBinding.instance.addPostFrameCallback((_) {
      _uiIsInitializing = false;
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
    // Directly switch to the requested rout if the UI is already initialized (=normal case),
    // but delay it if it is not (i.e. before the initial page is shown).
    if (!_uiIsInitializing) {
      unawaited(navigatorKey.currentState!.pushNamed(routeString, arguments: routeArguments));
    } else {
      SchedulerBinding.instance.addPostFrameCallback((_) {
        unawaited(navigatorKey.currentState!.pushNamed(routeString, arguments: routeArguments));
      });
    }
  }
}
