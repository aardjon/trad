///
/// Provides the nearby summit page widget of the *Route DB* domain.
///
library;

import 'package:adapters/boundaries/ui.dart';
import 'package:flutter/material.dart';

import '../state.dart';
import '../widgets/listviews.dart';

/// Widget representing the *Nearby Summits* page.
///
/// Note: This is *not* the similar tab which is part of the summit details page
class NearbySummitsPage extends StatelessWidget {
  /// The app drawer (navigation menu) to use.
  final Widget _appDrawer;

  /// Notifier providing the current summit list data to be displayed.
  final DeferableOptionalDataListNotifier _summitListNotifier;

  /// Constructor for directly initializing all members.
  const NearbySummitsPage(this._appDrawer, this._summitListNotifier, {super.key});

  @override
  Widget build(BuildContext context) {
    final NearbySummitsPageLabels model =
        ModalRoute.of(context)!.settings.arguments! as NearbySummitsPageLabels;
    return Scaffold(
      appBar: _appBar(model),
      body: SummitListView(_summitListNotifier),
      drawer: _appDrawer,
      drawerEnableOpenDragGesture: false,
    );
  }

  AppBar _appBar(NearbySummitsPageLabels model) {
    return AppBar(
      title: Text(model.pageTitle),
      centerTitle: true,
      backgroundColor: Colors.lightGreen,
    );
  }
}
