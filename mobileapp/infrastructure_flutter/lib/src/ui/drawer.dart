import 'package:flutter/material.dart';

import 'package:adapters/boundaries/ui.dart';
import 'package:adapters/controllers.dart';

import 'icons.dart';

/// Factory for creating the global application drawer.
class TradDrawerFactory {
  /// Model for the application main menu data.
  final MainMenuModel _model;

  /// Controller instance to notify for any user interaction.
  final ApplicationWideController _controller;

  final IconWidgetFactory _iconFactory = const IconWidgetFactory();

  /// Constructor for directly initializing all members.
  TradDrawerFactory(this._model, this._controller);

  /// Creates and returns a new instance of the application drawer for the given build [context].
  NavigationDrawer create(BuildContext context) {
    List<Widget> itemList = <Widget>[
      DrawerHeader(
        decoration: const BoxDecoration(
          color: Colors.lightGreen,
        ),
        child: Text(_model.menuHeader),
      ),
      ListTile(
        leading: _iconFactory.getIconWidget(_model.journalItem.icon),
        title: Text(_model.journalItem.mainTitle),
        onTap: _controller.requestSwitchToJournal,
      ),
      ListTile(
        leading: _iconFactory.getIconWidget(_model.routedbItem.icon),
        title: Text(_model.routedbItem.mainTitle),
        onTap: _controller.requestSwitchToRouteDb,
      ),
      ListTile(
        leading: _iconFactory.getIconWidget(_model.knowledgebaseItem.icon),
        title: Text(_model.knowledgebaseItem.mainTitle),
        onTap: _controller.requestSwitchToKnowledgebase,
      ),
      ListTile(
        leading: _iconFactory.getIconWidget(_model.settingsItem.icon),
        title: Text(_model.settingsItem.mainTitle),
        onTap: _controller.requestSwitchToSettings,
      ),
    ];
    return NavigationDrawer(children: itemList);
  }
}
