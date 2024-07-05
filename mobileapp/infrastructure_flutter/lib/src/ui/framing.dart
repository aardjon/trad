///
/// Contains the general framing of the GUI, i.e. the main widget itself as well as central UI
/// elements that are available on all pages.
///
library;

import 'package:flutter/material.dart';

import 'package:adapters/boundaries/ui.dart';
import 'package:adapters/controllers.dart';

import 'about.dart';
import 'drawer.dart';
import 'journal.dart';
import 'knowledgebase.dart';
import 'routedb.dart';
import 'routes.dart';
import 'state.dart';

/// The applications main widget.
///
/// This is the root widget of the whole GUI, all domain pages are mounted somewhere within its
/// child hierarchy.
class MainWidget extends StatelessWidget {
  /// The application's display name.
  final String _appName;

  /// The splash massage to display during initialization.
  final String _splashMessage;

  /// Mapping of display labels to the various domains pages.
  final DomainLabelDefinition _domainLabels;

  /// Factory for creating drawer (=navigation menu) instances as needed.
  final TradDrawerFactory _appDrawerFactory;

  /// Reference to the central state of the GUI.
  final GuiState _guiState;

  /// Constructor for directly initializing all members.
  MainWidget(
    String appName,
    String splashMessage,
    DomainLabelDefinition domainLabels,
    ApplicationWideController controller,
    GuiState guiState, {
    super.key,
  })  : _appName = appName,
        _splashMessage = splashMessage,
        _domainLabels = domainLabels,
        _appDrawerFactory = TradDrawerFactory(
          appName,
          domainLabels,
          controller,
        ),
        _guiState = guiState;

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: _appName,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.lightGreen),
        useMaterial3: true,
      ),
      routes: <String, WidgetBuilder>{
        UiRoute.journal.toRouteString(): (BuildContext context) {
          return JournalPage(
            _appDrawerFactory.create(context),
            _domainLabels.journalLabel,
          );
        },
        UiRoute.routedb.toRouteString(): (BuildContext context) {
          return RouteDbPage(
            _appDrawerFactory.create(context),
            _domainLabels.routedbLabel,
          );
        },
        UiRoute.knowledgebase.toRouteString(): (BuildContext context) {
          return KnowledgebaseView(_appDrawerFactory.create(context));
        },
        UiRoute.about.toRouteString(): (BuildContext context) {
          return AboutPage(
            _appDrawerFactory.create(context),
            _domainLabels.aboutLabel,
          );
        },
        UiRoute.splash.toRouteString(): (BuildContext context) {
          return _SplashPage(_splashMessage);
        },
      },
      initialRoute: UiRoute.splash.toRouteString(),
      navigatorKey: _guiState.getNavigatorKey(),
    );
  }
}

/// Splash widget simply showing the given message and not allowing any user interactions.
///
/// The message should be something like "loading...". This is meant to be shown only during
/// start up, right before switching to the initial page. In other words: If the app startup is
/// fast enough, no user shall ever see this page :)
class _SplashPage extends StatelessWidget {
  /// The message to be shown.
  final String _message;

  const _SplashPage(this._message);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: <Widget>[
            Text(
              _message,
            ),
          ],
        ),
      ),
    );
  }
}
