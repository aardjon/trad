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
      case Glyph.logoJournal:
        return const Icon(Icons.event_note);
      case Glyph.logoKnowledgeBase:
        return const Icon(Icons.school);
      case Glyph.logoRouteDb:
        return const Icon(Icons.landscape);
      case Glyph.logoSettings:
        return const Icon(Icons.settings);
      case Glyph.scoreLowest:
        return _getRatingIcon(Icons.star_border, iconDefinition.colorHint);
      case Glyph.scoreLowerMid:
        return _getRatingIcon(Icons.star_half, iconDefinition.colorHint);
      case Glyph.scoreUpperMid:
        return _getRatingIcon(Icons.star, iconDefinition.colorHint);
      case Glyph.scoreHighest:
        return _getRatingIcon(Icons.hotel_class, iconDefinition.colorHint);
    }
  }

  /// Create an Icon (widget) displaying the requested [colorHint] of the given [iconData].
  Icon _getRatingIcon(IconData iconData, ColorHint colorHint) {
    Color? color;
    switch (colorHint) {
      case ColorHint.neutral:
        color = Colors.grey;
      case ColorHint.greenPositive:
        color = Colors.green;
      case ColorHint.redNegative:
        color = Colors.red;
      case ColorHint.unspecified:
        color = null;
    }
    return Icon(iconData, color: color);
  }
}
