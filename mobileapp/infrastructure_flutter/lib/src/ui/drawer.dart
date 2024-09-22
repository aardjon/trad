import 'package:flutter/material.dart';

import 'package:adapters/boundaries/ui.dart';
import 'package:adapters/controllers.dart';

/// Factory for creating the global application drawer.
class TradDrawerFactory {
  /// The application name (displayed in the drawer header).
  final String _appName;

  /// Model for the application main menu data.
  final MainMenuModel _model;

  /// Controller instance to notify for any user interaction.
  final ApplicationWideController _controller;

  /// Constructor for directly initializing all members.
  TradDrawerFactory(this._appName, this._model, this._controller);

  /// Creates and returns a new instance of the application drawer for the given build [context].
  NavigationDrawer create(BuildContext context) {
    List<Widget> itemList = <Widget>[
      DrawerHeader(
        decoration: const BoxDecoration(
          color: Colors.lightGreen,
        ),
        child: Text(_appName),
      ),
      ListTile(
        title: Text(_model.journalLabel),
        onTap: _controller.requestSwitchToJournal,
      ),
      ListTile(
        title: Text(_model.routedbLabel),
        onTap: _controller.requestSwitchToRouteDb,
      ),
      ListTile(
        title: Text(_model.knowledgebaseLabel),
        onTap: _controller.requestSwitchToKnowledgebase,
      ),
      ListTile(
        title: Text(_model.aboutLabel),
        onTap: _controller.requestSwitchToAbout,
      ),
    ];
    return NavigationDrawer(children: itemList);
  }
}
