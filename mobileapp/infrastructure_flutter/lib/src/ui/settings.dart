///
/// Provides the *Settings* page widget.
///
library;

import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'package:adapters/boundaries/ui.dart';
import 'package:adapters/controllers.dart';

import 'state.dart';

/// Widget representing the *Settings* page.
class SettingsPage extends StatelessWidget {
  /// The app drawer (navigation menu) to use.
  final NavigationDrawer _appDrawer;

  /// The page title
  final String _title;

  /// Notifier providing the current settings state to be displayed.
  final SettingsNotifier _settingsState;

  /// Controller to notify about user actions regarding the route db.
  final RouteDbController _routeDbController;

  /// Constructor for directly initializing all members.
  SettingsPage(this._appDrawer, this._title, this._settingsState, {super.key})
      : _routeDbController = RouteDbController();

  @override
  Widget build(BuildContext context) {
    final SettingsModel model = ModalRoute.of(context)!.settings.arguments! as SettingsModel;

    return Scaffold(
      appBar: AppBar(
        backgroundColor: Theme.of(context).colorScheme.inversePrimary,
        title: Text(_title),
      ),
      body: ChangeNotifierProvider<SettingsNotifier>.value(
        value: _settingsState,
        child: Consumer<SettingsNotifier>(
          builder: (BuildContext context, SettingsNotifier state, Widget? child) {
            List<Widget> widgetList = <Widget>[
              const SizedBox(height: 10),
            ];
            if (state.getRouteDbAvailabilityMessage() != null) {
              widgetList.addAll(<Widget>[
                Card(
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Text(
                      state.getRouteDbAvailabilityMessage()!,
                      style: const TextStyle(color: Colors.red),
                      softWrap: true,
                    ),
                  ),
                ),
                const SizedBox(height: 30),
              ]);
            }
            widgetList.addAll(<Widget>[
              Text('${model.routeDbIdLabel} ${state.getRouteDbIdentifier()}'),
              const SizedBox(height: 10),
              ElevatedButton(
                child: Text(model.routeDbFileSelectionActionLabel),
                onPressed: () async {
                  FilePickerResult? result = await FilePicker.platform.pickFiles(
                    dialogTitle: model.routeDbFileSelectionFieldLabel,
                    allowMultiple: false,
                  );
                  if (result != null) {
                    String filePath = result.files.single.path!;
                    _routeDbController.requestRouteDbFileImport(filePath);
                  } // else: User cancelled the picker
                },
              ),
            ]);
            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.start,
                children: widgetList,
              ),
            );
          },
        ),
      ),
      drawer: _appDrawer,
    );
  }
}
