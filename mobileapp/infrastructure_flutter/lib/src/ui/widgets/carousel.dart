///
/// Provides a simple "carousel" widget which always shows one of several possible items, together
/// with a possibility to switch between them.
///
library;

import 'package:flutter/material.dart';

/// A widget containing several child widgets but showing only one of them at a time. The widgets
/// being available are defined statically and cannot be changed later. Two navigation buttons allow
/// to switch between the widgets, but there is no transition animation or "partial display"
/// feature.
///
/// If only one child widget is provided at all, it is displayed as-is without the navigation
/// buttons.
///
/// The WidgetCarousel always takes up the space needed to display its largest child.
class WidgetCarousel extends StatefulWidget {
  final List<Widget> _items;

  /// Constructor for creating a new carousel widget. The first parameter takes all child widgets
  /// that can be displayed by this carousel. The provided widget list must not be empty.
  WidgetCarousel(this._items, {super.key})
    : assert(_items.isNotEmpty, 'Carousel items list must not be empty.');

  /// Returns all child widgets that can be displayed by this carousel.
  List<Widget> get items => _items;

  @override
  State<StatefulWidget> createState() {
    return _WidgetCarouselState();
  }
}

/// Current state of a [WidgetCarousel], mainly the widget that is being displayed.
class _WidgetCarouselState extends State<WidgetCarousel> {
  int currentWidgetIndex = 0;

  @override
  Widget build(BuildContext context) {
    if (widget.items.length > 1) {
      return Row(
        crossAxisAlignment: CrossAxisAlignment.center,
        children: <Widget>[
          IconButton(
            padding: EdgeInsets.zero,
            icon: const Icon(Icons.chevron_left),
            onPressed: () {
              setState(() {
                currentWidgetIndex = (currentWidgetIndex - 1) % widget.items.length;
              });
            },
          ),

          Expanded(
            child: IndexedStack(
              index: currentWidgetIndex,
              children: widget.items,
            ),
          ),

          IconButton(
            padding: EdgeInsets.zero,
            icon: const Icon(Icons.chevron_right),
            onPressed: () {
              setState(() {
                currentWidgetIndex = (currentWidgetIndex + 1) % widget.items.length;
              });
            },
          ),
        ],
      );
    } else {
      return Padding(padding: const EdgeInsets.symmetric(horizontal: 24), child: widget.items[0]);
    }
  }
}
