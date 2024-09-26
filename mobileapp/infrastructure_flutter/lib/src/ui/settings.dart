///
/// Provides the *Settings* page widget.
///
library;

import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';

import 'package:adapters/boundaries/ui.dart';
import 'package:adapters/controllers.dart';

/// Widget representing the *Settings* page.
class SettingsPage extends StatelessWidget {
  /// The app drawer (navigation menu) to use.
  final NavigationDrawer _appDrawer;

  /// The page title
  final String _title;

  /// Controller to notify about user actions regarding the route db.
  final RouteDbController _routeDbController;

  /// Constructor for directly initializing all members.
  SettingsPage(this._appDrawer, this._title, {super.key})
      : _routeDbController = RouteDbController();

  @override
  Widget build(BuildContext context) {
    final SettingsModel model = ModalRoute.of(context)!.settings.arguments! as SettingsModel;

    return Scaffold(
      appBar: AppBar(
        backgroundColor: Theme.of(context).colorScheme.inversePrimary,
        title: Text(_title),
      ),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: <Widget>[
            Text('${model.routeDbIdLabel} ${model.routeDbIdentifier}'),
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
          ],
        ),
      ),
      drawer: _appDrawer,
    );
  }
}
