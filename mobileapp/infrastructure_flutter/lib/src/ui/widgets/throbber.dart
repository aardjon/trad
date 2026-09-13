///
/// Provides a loading animation widget that can be used whenever the user has
/// to wait for a pending operation.
///
library;

import 'package:flutter/material.dart';
import 'package:loading_indicator/loading_indicator.dart';

/// A widget that displays a loading animation, signalling the user that he has
/// to wait for something. The widget can optionally display an additional text
/// message.
class Throbber extends StatelessWidget {
  /// Optional message to display to the user, in addition to the animation.
  /// If null, no text is displayed (and no space is reserved for it).
  final String? message;

  /// Optional height value of the widget. If given, the widget height is set to
  /// this value and its width is calculated automaticall. If null, the widget
  /// uses the available space.
  final double? fixedHeight;

  /// Constructor for directly initializing all members.
  const Throbber({this.message, this.fixedHeight, super.key});

  @override
  Widget build(BuildContext context) {
    const LoadingIndicator loadingIndicator = LoadingIndicator(
      indicatorType: Indicator.ballClipRotateMultiple,
      colors: <Color>[Colors.lightGreen],
    );
    List<Widget> widgets = <Widget>[
      if (fixedHeight != null)
        SizedBox(
          height: fixedHeight,
          child: loadingIndicator,
        )
      else
        loadingIndicator,
    ];

    if (message != null) {
      widgets.add(Text(message!));
    }
    return widgets.length > 1 ? Column(children: widgets) : widgets[0];
  }
}
