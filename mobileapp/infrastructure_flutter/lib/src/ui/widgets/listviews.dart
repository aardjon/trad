///
/// Provides widgets for displaying lists of data.
///
/// This includes generic, reusable base clases as well as concrete implementations for certain
/// situations.
///
library;

import 'package:adapters/boundaries/ui.dart';
import 'package:adapters/controllers.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../state.dart';
import 'centered_text.dart';
import 'throbber.dart';

/// Reusable widget for displaying a list of summits provided by a [DeferableOptionalDataListNotifier].
class SummitListView extends StatelessWidget {
  /// The notifier providing the data.
  final DeferableOptionalDataListNotifier _dataNotifier;

  /// Constructor for directly initializing all members.
  const SummitListView(this._dataNotifier, {super.key});

  @override
  Widget build(BuildContext context) {
    return DeferableOptionalDataListView(_dataNotifier, _buildSummitTile);
  }

  /// Build the (single) data row widget of view index [index] for the data from the given
  /// [notifier].
  ListTile _buildSummitTile(DeferableOptionalDataListNotifier notifier, int index) {
    final ListViewItem summit = notifier.getDataItem(index);
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

/// A generic list view widget that displays a list of item coming from a Notifier(=model). If the
/// data is not loaded yet, it displays a throbber animation. If (after loading) there is no data
/// to display, it shows an alternative text message.
///
/// To use this class, it is necessary to provide a concrete list item builder. The common approach
/// is to derive from it so that the builder function and event handlers can be in one place.
class DeferableOptionalDataListView extends StatelessWidget {
  /// Notifier providing the current data to be displayed.
  final DeferableOptionalDataListNotifier _dataNotifier;

  /// Function that creates the list item widget for the data item with the given index from the
  /// given notifier/model.
  final Widget Function(DeferableOptionalDataListNotifier, int) _listItemBuilder;

  /// Constructor for directly initializing all members.
  const DeferableOptionalDataListView(this._dataNotifier, this._listItemBuilder, {super.key});

  @override
  Widget build(BuildContext context) {
    return ChangeNotifierProvider<DeferableOptionalDataListNotifier>.value(
      value: _dataNotifier,
      child: Consumer<DeferableOptionalDataListNotifier>(
        builder: (BuildContext context, DeferableOptionalDataListNotifier notifier, Widget? child) {
          if (_dataNotifier.dataLoaded) {
            if (_dataNotifier.canDisplayData()) {
              return _buildListView(notifier, context);
            } else {
              return _buildEmptyDataFallback(notifier);
            }
          } else {
            return _buildLoadingIndicator();
          }
        },
      ),
    );
  }

  Widget _buildEmptyDataFallback(OptionalDataListNotifier notifier) {
    return CenteredText(notifier.fallbackMessage);
  }

  Widget _buildLoadingIndicator() {
    return const Throbber();
  }

  Widget _buildListView(DeferableOptionalDataListNotifier notifier, BuildContext context) {
    return ListView.builder(
      itemCount: notifier.getDataItemCount(),
      itemBuilder: (BuildContext context, int index) {
        return _listItemBuilder(notifier, index);
      },
    );
  }
}
