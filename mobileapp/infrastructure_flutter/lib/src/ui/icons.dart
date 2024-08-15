///
/// Provides a factory for creating icon widgets.
///
library;

import 'package:flutter/material.dart';

import 'package:adapters/boundaries/ui.dart';

/// Factory creating Widgets for displaying [IconDefinition]s.
class IconWidgetFactory {
  /// Const default constructor (to improve performance).
  const IconWidgetFactory();

  /// Create and return a widget that displays the given [iconDefinition].
  Widget getIconWidget(IconDefinition? iconDefinition) {
    if (iconDefinition == null) {
      return const Icon(null);
    }
    switch (iconDefinition.glyph) {
      case Glyph.checked:
        return const Icon(Icons.done);
      case Glyph.scoreLowest:
        return _getRatingIcon(Icons.star_border, iconDefinition.mood);
      case Glyph.scoreLowerMid:
        return _getRatingIcon(Icons.star_half, iconDefinition.mood);
      case Glyph.scoreUpperMid:
        return _getRatingIcon(Icons.star, iconDefinition.mood);
      case Glyph.scoreHighest:
        return _getRatingIcon(Icons.hotel_class, iconDefinition.mood);
    }
  }

  /// Create an Icon (widget) displaying the requested [mood] of the given [iconData].
  Icon _getRatingIcon(IconData iconData, Mood mood) {
    Color? color;
    switch (mood) {
      case Mood.neutral:
        color = Colors.grey;
      case Mood.positive:
        color = Colors.green;
      case Mood.negative:
        color = Colors.red;
      case Mood.unspecified:
        color = null;
    }
    return Icon(iconData, color: color);
  }
}
