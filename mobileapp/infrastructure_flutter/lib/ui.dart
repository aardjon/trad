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

import 'src/ui/framing.dart';
import 'src/ui/routes.dart';

/// Implementation of the boundary interface used by the `adapters` to communicate with the concrete
/// UI.
///
/// This is basically an adapter which delegates all calls to the corresponding Flutter/widget
/// operation.
class ApplicationUI implements ApplicationUiBoundary {
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
  }

  @override
  void switchToRouteDb() {
    SchedulerBinding.instance.addPostFrameCallback((_) {
      unawaited(navigatorKey.currentState!.pushNamed(UiRoute.routedb.toRouteString()));
    });
  }

  @override
  void switchToJournal() {
    SchedulerBinding.instance.addPostFrameCallback((_) {
      unawaited(navigatorKey.currentState!.pushNamed(UiRoute.journal.toRouteString()));
    });
  }

  @override
  void showKnowledgebase(KnowledgebaseModel document) {
    SchedulerBinding.instance.addPostFrameCallback((_) {
      unawaited(
        navigatorKey.currentState!
            .pushNamed(UiRoute.knowledgebase.toRouteString(), arguments: document),
      );
    });
  }

  @override
  void switchToAbout() {
    SchedulerBinding.instance.addPostFrameCallback((_) {
      unawaited(navigatorKey.currentState!.pushNamed(UiRoute.about.toRouteString()));
    });
  }
}
