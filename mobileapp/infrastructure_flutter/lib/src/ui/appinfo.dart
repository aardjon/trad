///
/// Provides the *About this app* page widget.
///
library;

import 'package:adapters/boundaries/ui.dart';
import 'package:adapters/controllers.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'state.dart';

/// Widget representing the *About* page.
class AppInfoPage extends StatelessWidget {
  /// The app drawer (navigation menu) to use.
  final Widget _appDrawer;

  /// Notifier providing the current settings state to be displayed.
  final SettingsNotifier _settingsState;

  /// Constructor for directly initializing all members.
  const AppInfoPage(this._appDrawer, this._settingsState, {super.key});

  Widget _buildAppVersionLabel(BuildContext context, AppInfoModel model) {
    return Padding(
      padding: const EdgeInsets.only(top: 15, bottom: 5),
      child: Center(
        child: Text(
          model.versionLabel,
          style: Theme.of(context).textTheme.titleLarge,
        ),
      ),
    );
  }

  List<Widget> _buildAppInfoWidgets(BuildContext context, AppInfoModel model) {
    final TextStyle? labelStyle = Theme.of(context).textTheme.bodyMedium;
    List<Widget> widgets = <Widget>[_buildAppVersionLabel(context, model)];
    for (final String label in model.copyrightAttributionLabels) {
      widgets.add(Center(child: Text(label, style: labelStyle)));
    }
    widgets.add(
      ElevatedButton(
        onPressed: _onShowHomepageClicked,
        child: Text(model.websiteButtonLabel),
      ),
    );
    return widgets;
  }

  List<Widget> _buildRouteDbSourcesList(BuildContext context, SettingsNotifier state) {
    List<Widget> listWidgets = <Widget>[];
    for (final ListViewItem source in state.getDataSourceAttributions()) {
      listWidgets.add(
        ListTile(
          title: Text(
            source.mainTitle,
            style: Theme.of(context).textTheme.bodyLarge,
            textAlign: TextAlign.start,
          ),
          subtitle: Text(
            '${source.subTitle}\n${source.content}',
            style: Theme.of(context).textTheme.bodyMedium,
            textAlign: TextAlign.start,
          ),
          dense: true,
          contentPadding: const EdgeInsets.symmetric(vertical: 0, horizontal: 16),
          onTap: () {
            _onExternalSourceClicked(source.itemId!);
          },
        ),
      );
    }
    return listWidgets;
  }

  List<Widget> _buildRouteDbInfoWidgets(BuildContext context, AppInfoModel model) {
    final TextStyle? labelStyle = Theme.of(context).textTheme.bodyMedium;

    return <Widget>[
      Padding(
        padding: const EdgeInsets.only(top: 15, bottom: 5),
        child: Center(
          child: Text(
            model.routeDataHeader,
            style: Theme.of(context).textTheme.titleLarge,
          ),
        ),
      ),
      ChangeNotifierProvider<SettingsNotifier>.value(
        value: _settingsState,
        child: Consumer<SettingsNotifier>(
          builder: (BuildContext context, SettingsNotifier state, Widget? child) {
            if (state.getDataSourceAttributions().isNotEmpty) {
              List<Widget> widgetList = <Widget>[
                Text(
                  model.routeDataSourcesLabel,
                  textAlign: TextAlign.start,
                  style: labelStyle,
                ),
                Column(
                  children: _buildRouteDbSourcesList(context, state),
                ),
                Text(
                  model.routeDataDisclaimer,
                  textAlign: TextAlign.start,
                  style: labelStyle!.apply(fontSizeFactor: 0.8),
                ),
              ];
              return Column(mainAxisAlignment: MainAxisAlignment.start, children: widgetList);
            }
            return Text(model.noRouteDataMessage, style: labelStyle);
          },
        ),
      ),
    ];
  }

  List<Widget> _buildSupportWidgets(BuildContext context, AppInfoModel model) {
    final TextStyle? labelStyle = Theme.of(context).textTheme.bodyMedium;
    List<Widget> widgets = <Widget>[
      Padding(
        padding: const EdgeInsets.only(top: 15, bottom: 5),
        child: Center(
          child: Text(
            model.supportHeader,
            style: Theme.of(context).textTheme.titleLarge,
          ),
        ),
      ),
    ];
    for (final String line in model.supportLabels) {
      widgets.add(Center(child: Text(line, style: labelStyle)));
    }
    return widgets;
  }

  @override
  Widget build(BuildContext context) {
    final AppInfoModel model = ModalRoute.of(context)!.settings.arguments! as AppInfoModel;

    return Scaffold(
      appBar: AppBar(
        backgroundColor: Theme.of(context).colorScheme.inversePrimary,
        title: Text(model.pageTitle),
      ),
      body: Center(
        child: ListView(
          shrinkWrap: true,
          children:
              _buildAppInfoWidgets(context, model) +
              _buildRouteDbInfoWidgets(context, model) +
              _buildSupportWidgets(context, model),
        ),
      ),
      drawer: _appDrawer,
    );
  }

  /// Event handler for clicking the 'Open the trad web site' button.
  void _onShowHomepageClicked() {
    ApplicationWideController controller = ApplicationWideController();
    controller.requestAppHomepage();
  }

  /// Event handler for clicking a single data source list item. [sourceId] is the internal ID of
  /// this source.
  void _onExternalSourceClicked(int sourceId) {
    ApplicationWideController controller = ApplicationWideController();
    controller.requestExternalSource(sourceId);
  }
}
