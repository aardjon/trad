import 'package:flutter/material.dart';

import 'package:adapters/boundaries/ui.dart';
import 'package:adapters/controllers.dart';
import 'package:provider/provider.dart';

import 'icons.dart';
import 'state.dart';

/// Factory for creating the global application drawer.
class TradDrawerFactory {
  /// Model for the application main menu data.
  final MainMenuModel _model;

  /// Notifier providing the current settings state to be displayed.
  final SettingsNotifier _settingsState;

  /// Controller instance to notify for any user interaction.
  final ApplicationWideController _controller;

  final IconWidgetFactory _iconFactory = const IconWidgetFactory();

  /// Constructor for directly initializing all members.
  TradDrawerFactory(this._model, this._settingsState, this._controller);

  /// Creates and returns a new instance of the application drawer for the given build [context].
  Widget create(BuildContext context) {
    ChangeNotifierProvider<SettingsNotifier> changeNotifier =
        ChangeNotifierProvider<SettingsNotifier>.value(
          value: _settingsState,
          child: Consumer<SettingsNotifier>(
            builder: (BuildContext context, SettingsNotifier state, Widget? child) {
              List<Widget> itemList = <Widget>[
                DrawerHeader(
                  decoration: const BoxDecoration(color: Colors.lightGreen),
                  child: Column(
                    children: <Widget>[
                      const Image(
                        image: AssetImage('assets/logo.png', package: 'infrastructure_flutter'),
                        width: 100,
                        height: 100,
                      ),
                      Text(_model.menuHeader),
                    ],
                  ),
                ),
                /*ListTile(
                  leading: _iconFactory.getIconWidget(_model.journalItem.icon),
                  title: Text(_model.journalItem.mainTitle),
                  onTap: _controller.requestSwitchToJournal,
                ),*/
                ListTile(
                  enabled: _settingsState.isRouteDbAavailable(),
                  leading: _iconFactory.getIconWidget(_model.routedbItem.icon),
                  title: Text(_model.routedbItem.mainTitle),
                  onTap: _controller.requestSwitchToRouteDb,
                ),
                /*ListTile(
                  leading: _iconFactory.getIconWidget(_model.knowledgebaseItem.icon),
                  title: Text(_model.knowledgebaseItem.mainTitle),
                  onTap: _controller.requestSwitchToKnowledgebase,
                ),*/
                const Divider(),
                ListTile(
                  leading: _iconFactory.getIconWidget(_model.settingsItem.icon),
                  title: Text(_model.settingsItem.mainTitle),
                  onTap: _controller.requestSwitchToSettings,
                ),
              ];
              return NavigationDrawer(children: itemList);
            },
          ),
        );
    return changeNotifier;
  }
}
