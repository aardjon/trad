///
/// Provides a widget for showing an alternate message in case the requested data cannot be
/// displayed.
///
library;

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../state.dart';

/// This widget wraps another widget which is usually displayed. But when there is no data to
/// display for some reason (as indicated by the Notifier), it displays the given message instead.
class OptionalDataView extends StatelessWidget {
  // The notifier (state) object providing the data to display (or not).
  final AlternateStatusMessageNotifier _notifier;

  /// Builder function creating the reguarly, data-displaying child widget.
  final Widget Function(BuildContext) _childBuilder;

  /// Constructor for directly initializing all members.
  const OptionalDataView(this._notifier, {required this._childBuilder, super.key});

  @override
  Widget build(BuildContext context) {
    return ChangeNotifierProvider<AlternateStatusMessageNotifier>.value(
      value: _notifier,
      child: Consumer<AlternateStatusMessageNotifier>(
        builder: (BuildContext context, AlternateStatusMessageNotifier state, Widget? child) {
          if (state.canDisplayData()) {
            return _childBuilder(context);
          } else {
            return _buildNoDataMessageWidget();
          }
        },
      ),
    );
  }

  /// Build the alternative Widget displaying the given message.
  Widget _buildNoDataMessageWidget() {
    return Column(
      mainAxisAlignment: MainAxisAlignment.center,
      children: <Widget>[
        Center(
          child: Padding(
            padding: const EdgeInsets.all(20),
            child: Text(_notifier.getAlternateMessage()),
          ),
        ),
      ],
    );
  }
}
