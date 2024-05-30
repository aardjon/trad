///
/// Contains the general framing of the GUI, i.e. the main widget itself as well as central UI
/// elements that are available on all pages.
///
library;

import 'package:flutter/material.dart';

import 'package:adapters/boundaries/ui.dart';
import 'package:adapters/controllers/global.dart';

import 'about.dart';
import 'drawer.dart';
import 'journal.dart';
import 'knowledgebase.dart';
import 'routedb.dart';
import 'routes.dart';

/// Global navigation key for switching between pages without having a `context` object.
final GlobalKey<NavigatorState> navigatorKey = GlobalKey<NavigatorState>();

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

  /// Factory for creating drawer (=navigaiton menu) instances as needed.
  final TradDrawerFactory _appDrawerFactory;

  MainWidget(
    String appName,
    String splashMessage,
    DomainLabelDefinition domainLabels,
    ApplicationWideController controller, {
    super.key,
  })  : _appName = appName,
        _splashMessage = splashMessage,
        _domainLabels = domainLabels,
        _appDrawerFactory = TradDrawerFactory(
          appName,
          domainLabels,
          controller,
        );

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: _appName,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.lightGreen),
        useMaterial3: true,
      ),
      routes: {
        UiRoute.journal.toRouteString(): (context) {
          return JournalPage(
            _appDrawerFactory.create(context),
            _domainLabels.journalLabel,
          );
        },
        UiRoute.routedb.toRouteString(): (context) {
          return RouteDbPage(
            _appDrawerFactory.create(context),
            _domainLabels.routedbLabel,
          );
        },
        UiRoute.knowledgebase.toRouteString(): (context) {
          return KnowledgebaseView(
            _appDrawerFactory.create(context),
            _domainLabels.knowledgebaseLabel,
          );
        },
        UiRoute.about.toRouteString(): (context) {
          return AboutPage(
            _appDrawerFactory.create(context),
            _domainLabels.aboutLabel,
          );
        },
        UiRoute.splash.toRouteString(): (context) {
          return _SplashPage(_splashMessage);
        },
      },
      initialRoute: UiRoute.splash.toRouteString(),
      navigatorKey: navigatorKey,
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
