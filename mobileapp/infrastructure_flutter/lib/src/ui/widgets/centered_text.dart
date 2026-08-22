///
/// Provides a widget for showing a centered text message, e.g. in case the requested data cannot
/// be displayed.
///
library;

import 'package:flutter/material.dart';

/// Simple text widget that displays the given text centered and padded. Used to easily maintain a
/// unified look in all such situations.
class CenteredText extends StatelessWidget {
  /// The text to display.
  final String _message;

  /// Constructor for directly initializing all members.
  const CenteredText(this._message, {super.key});

  @override
  Widget build(BuildContext context) {
    return Column(
      mainAxisAlignment: MainAxisAlignment.center,
      children: <Widget>[
        Center(
          child: Padding(
            padding: const EdgeInsets.all(20),
            child: Text(_message),
          ),
        ),
      ],
    );
  }
}
