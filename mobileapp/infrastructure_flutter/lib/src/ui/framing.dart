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
import 'routedb/route_details.dart';
import 'routedb/summit_details.dart';
import 'routedb/summit_list.dart';
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

  /// Model for the app's main menu (drawer).
  final MainMenuModel _menuModel;

  /// Factory for creating drawer (=navigation menu) instances as needed.
  final TradDrawerFactory _appDrawerFactory;

  /// Reference to the central state of the GUI.
  final GuiState _guiState;

  /// Reference to the central summit list state notifier.
  final SummitListNotifier _summitListState;

  final RouteListNotifier _routeListState;

  final PostListNotifier _postListState;

  /// Constructor for directly initializing all members.
  MainWidget(
    String appName,
    String splashMessage,
    MainMenuModel menuModel,
    ApplicationWideController controller,
    GuiState guiState,
    SummitListNotifier summitListState,
    RouteListNotifier routeListState,
    PostListNotifier postListState, {
    super.key,
  })  : _appName = appName,
        _splashMessage = splashMessage,
        _menuModel = menuModel,
        _appDrawerFactory = TradDrawerFactory(
          appName,
          menuModel,
          controller,
        ),
        _guiState = guiState,
        _summitListState = summitListState,
        _routeListState = routeListState,
        _postListState = postListState;

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
            _menuModel.journalLabel,
          );
        },
        UiRoute.summitlist.toRouteString(): (BuildContext context) {
          return SummitListView(
            _appDrawerFactory.create(context),
            _summitListState,
          );
        },
        UiRoute.summitdetails.toRouteString(): (BuildContext context) {
          return SummitDetailsView(
            _appDrawerFactory.create(context),
            _routeListState,
          );
        },
        UiRoute.routedetails.toRouteString(): (BuildContext context) {
          return RouteDetailsView(
            _appDrawerFactory.create(context),
            _postListState,
          );
        },
        UiRoute.knowledgebase.toRouteString(): (BuildContext context) {
          return KnowledgebaseView(_appDrawerFactory.create(context));
        },
        UiRoute.about.toRouteString(): (BuildContext context) {
          return AboutPage(
            _appDrawerFactory.create(context),
            _menuModel.aboutLabel,
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
