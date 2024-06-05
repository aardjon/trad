import 'package:flutter/material.dart';

import 'package:adapters/boundaries/ui.dart';
import 'package:adapters/controllers.dart';

/// Factory for creating the global application drawer.
class TradDrawerFactory {
  /// The application name (displayed in the drawer header).
  final String _appName;
  /// Display labels of the application domain, used as menu item.
  final DomainLabelDefinition _domainLabels;
  /// Controller instance to notify for any user interaction.
  final ApplicationWideController _controller;

  /// Constructor for directly initializing all members.
  TradDrawerFactory(this._appName, this._domainLabels, this._controller);

  /// Creates and returns a new instance of the application drawer for the given build [context].
  NavigationDrawer create(BuildContext context) {
    List<Widget> itemList = [
      DrawerHeader(
        decoration: const BoxDecoration(
          color: Colors.lightGreen,
        ),
        child: Text(_appName),
      ),
      ListTile(
        title: Text(_domainLabels.journalLabel),
        onTap: () {
          _controller.requestSwitchToJournal();
        },
      ),
      ListTile(
        title: Text(_domainLabels.routedbLabel),
        onTap: () {
          _controller.requestSwitchToRouteDb();
        },
      ),
      ListTile(
        title: Text(_domainLabels.knowledgebaseLabel),
        onTap: () {
          _controller.requestSwitchToKnowledgebase();
        },
      ),
      ListTile(
        title: Text(_domainLabels.aboutLabel),
        onTap: () {
          _controller.requestSwitchToAbout();
        },
      ),
    ];
    return NavigationDrawer(children: itemList);
  }
}
