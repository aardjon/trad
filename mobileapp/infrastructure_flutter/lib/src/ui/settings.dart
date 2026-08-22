///
/// Provides the *Settings* page widget.
///
library;

import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:loading_indicator/loading_indicator.dart';
import 'package:provider/provider.dart';

import 'package:adapters/boundaries/ui.dart';
import 'package:adapters/controllers.dart';

import 'state.dart';

/// Widget representing the *Settings* page.
class SettingsPage extends StatelessWidget {
  /// The app drawer (navigation menu) to use.
  final Widget _appDrawer;

  /// The page title
  final String _title;

  /// Notifier providing the current routeDB state to be displayed.
  final RouteDbStatusNotifier _routeDbState;

  /// Constructor for directly initializing all members.
  const SettingsPage(this._appDrawer, this._title, this._routeDbState, {super.key});

  @override
  Widget build(BuildContext context) {
    final SettingsModel model = ModalRoute.of(context)!.settings.arguments! as SettingsModel;

    return Scaffold(
      appBar: AppBar(
        backgroundColor: Theme.of(context).colorScheme.inversePrimary,
        title: Text(_title),
      ),
      body: _RouteDbActionsWidget(settingsModel: model, routeDbState: _routeDbState),
      drawer: _appDrawer,
    );
  }
}

/// Widget representing the 'route database' section of the settings page.
class _RouteDbActionsWidget extends StatelessWidget {
  /// Notifier providing the current routeDB state to be displayed.
  final RouteDbStatusNotifier _routeDbState;

  /// Model providing static page data.
  final SettingsModel _settingsModel;

  /// Controller to notify about user actions regarding the route db.
  final RouteDbController _routeDbController;

  /// Constructor for directly initializing all members.
  _RouteDbActionsWidget({required this._settingsModel, required this._routeDbState})
    : _routeDbController = RouteDbController();

  @override
  Widget build(BuildContext context) {
    return ChangeNotifierProvider<RouteDbStatusNotifier>.value(
      value: _routeDbState,
      child: Center(
        child: Consumer<RouteDbStatusNotifier>(
          builder: (BuildContext context, RouteDbStatusNotifier state, Widget? child) {
            List<Widget> widgetList = <Widget>[
              Text(
                _settingsModel.routeDbSectionTitle,
                style:
                    DefaultTextStyle.of(
                      context,
                    ).style.apply(
                      fontSizeFactor: 1.2,
                      heightFactor: 1.5,
                      fontWeightDelta: 2,
                    ),
              ),
            ];
            if (state.isRouteDbUpdateInProgress()) {
              widgetList.addAll(
                _buildRouteDbUpdateTaskWidgets(_settingsModel.routeDbUpdateInProgressLabel),
              );
            } else {
              widgetList.addAll(_buildManageRouteDbWidgets(_settingsModel, state));
            }
            return Column(mainAxisAlignment: MainAxisAlignment.start, children: widgetList);
          },
        ),
      ),
    );
  }

  List<Widget> _buildRouteDbUpdateTaskWidgets(String inProgressLabel) {
    return <Widget>[
      const SizedBox(
        height: 100,
        child: LoadingIndicator(
          indicatorType: Indicator.ballClipRotateMultiple,
          colors: <Color>[Colors.lightGreen],
        ),
      ),
      Text(inProgressLabel),
    ];
  }

  List<Widget> _buildManageRouteDbWidgets(SettingsModel model, RouteDbStatusNotifier state) {
    List<Widget> widgetList = <Widget>[
      Text('${model.routeDbIdLabel} ${state.getRouteDbIdentifier()}'),
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
        //const SizedBox(height: 30),
      ]);
    }

    String? updateErrorMessage = state.popLastUpdateErrorMessage();
    if (updateErrorMessage != null) {
      widgetList.addAll(<Widget>[
        Card(
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Text(
              updateErrorMessage,
              style: const TextStyle(color: Colors.red),
              softWrap: true,
            ),
          ),
        ),
        //const SizedBox(height: 30),
      ]);
    }

    widgetList.addAll(<Widget>[
      const SizedBox(height: 10),
      ElevatedButton(
        child: Text(model.routeDbUpdateLabel),
        onPressed: () async {
          _routeDbController.requestRouteDbUpdate();
        },
      ),
      const SizedBox(height: 10),
      ElevatedButton(
        onPressed: _onImportLocalFile,
        child: Text(model.routeDbFileSelectionActionLabel),
      ),
    ]);

    return widgetList;
  }

  /// Called when the user chooses to import a local route DB file
  Future<void> _onImportLocalFile() async {
    PlatformFile? result = await FilePicker.pickFile(
      dialogTitle: _settingsModel.routeDbFileSelectionFieldLabel,
    );
    if (result != null) {
      String filePath = result.path!;
      _routeDbController.requestRouteDbFileImport(filePath);
    } // else: User cancelled the picker
  }
}
