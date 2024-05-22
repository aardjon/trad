///
/// Flutter implementation of trad's user interface.
///
/// This library is responsible for all UI look & feel, but must neither contain any business logic
/// nor any display strings. Concrete UI implementations shall be as dumb as possible!
///
library;

import 'package:flutter/material.dart';
import 'package:flutter/scheduler.dart';

import 'package:adapters/boundaries/ui.dart';
import 'package:adapters/controllers/global.dart';

import 'src/ui/framing.dart';
import 'src/ui/routes.dart';

/// Implementation of the boundary interface used by the `adapter` to communicate with the concrete
/// UI.
///
/// This is basically an adapter which delagates all call to the corresponding Flutter or widget
/// operation.
class ApplicationUI implements ApplicationUiBoundary {
  @override
  void initializeUserInterface(
    String appName,
    String splashString,
    DomainLabelDefinition routeLabels,
  ) {
    runApp(MainWidget(
      appName,
      splashString,
      routeLabels,
      ApplicationWideController(),
    ));
  }

  @override
  void switchToRouteDb() {
    SchedulerBinding.instance.addPostFrameCallback((_) {
      navigatorKey.currentState!.pushNamed(UiRoute.routedb.toRouteString());
    });
  }

  @override
  void switchToJournal() {
    SchedulerBinding.instance.addPostFrameCallback((_) {
      navigatorKey.currentState!.pushNamed(UiRoute.journal.toRouteString());
    });
  }

  @override
  void switchToKnowledgebase() {
    SchedulerBinding.instance.addPostFrameCallback((_) {
      navigatorKey.currentState!
          .pushNamed(UiRoute.knowledgebase.toRouteString());
    });
  }

  @override
  void switchToAbout() {
    SchedulerBinding.instance.addPostFrameCallback((_) {
      navigatorKey.currentState!.pushNamed(UiRoute.about.toRouteString());
    });
  }
}
