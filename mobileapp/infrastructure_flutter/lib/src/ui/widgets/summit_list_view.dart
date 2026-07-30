///
/// Provides a widget for displaying lists of summits.
///
library;

import 'package:adapters/boundaries/ui.dart';
import 'package:adapters/controllers.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../state.dart';

/// Reusable widget for displaying a list of summits provided by a [SummitListNotifier].
class SummitListView extends StatelessWidget {
  /// Notifier providing the current summit list state to be displayed.
  final SummitListNotifier _summitListNotifer;

  /// Constructor for directly initializing all members.
  const SummitListView(this._summitListNotifer, {super.key});

  @override
  Widget build(BuildContext context) {
    //final SummitListModel model = ModalRoute.of(context)!.settings.arguments! as SummitListModel;
    return ChangeNotifierProvider<SummitListNotifier>.value(
      value: _summitListNotifer,
      child: Consumer<SummitListNotifier>(
        builder: (BuildContext context, SummitListNotifier model, Widget? child) {
          return ListView.builder(
            itemCount: model.getSummitCount(),
            itemBuilder: (BuildContext context, int index) {
              final ListViewItem summit = model.getSummitItem(index);
              return _buildSummitTile(summit);
            },
          );
        },
      ),
    );
  }

  ListTile _buildSummitTile(ListViewItem summit) {
    return ListTile(
      title: Text(summit.mainTitle),
      trailing: Text(summit.subTitle ?? ''),
      onTap: () {
        _onSummitTap(summit.itemId!);
      },
    );
  }

  /// Callback function that is called when the user taps on a single item. [summitDataId] is the data
  /// item ID of the tapped summit.
  void _onSummitTap(ItemDataId summitDataId) {
    RouteDbController controller = RouteDbController();
    controller.requestSummitDetails(summitDataId);
  }
}
