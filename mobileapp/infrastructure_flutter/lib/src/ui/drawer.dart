import 'package:adapters/controllers/global.dart';
import 'package:adapters/boundaries/ui.dart';
import 'package:flutter/material.dart';

class TradDrawerFactory {
  final String _appName;
  final DomainLabelDefinition _domainLabels;
  final ApplicationWideController _controller;

  TradDrawerFactory(this._appName, this._domainLabels, this._controller);

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
