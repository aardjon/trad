///
/// Provides a factory for mapping ratings to icon definitions.
///
library;

import '../../boundaries/ui.dart';

/// Factory for creating IconDefinition instances representing different ratings.
class RatingIconFactory {
  /// Const default constructor (to improve performance).
  const RatingIconFactory();

  /// Mapping of glyphs to rating values.
  static const Map<int, Glyph> _glyphMapping = <int, Glyph>{
    3: Glyph.scoreHighest,
    2: Glyph.scoreUpperMid,
    1: Glyph.scoreLowerMid,
    0: Glyph.scoreLowest,
  };

  /// Create the IconDefinition describing the given [rating] value.
  IconDefinition getDoubleRatingIcon(double rating) {
    return getIntRatingIcon(rating.round());
  }

  /// Create the IconDefinition describing the given [rating] value.
  IconDefinition getIntRatingIcon(int rating) {
    final Glyph glyph = _glyphMapping[rating.clamp(-3, 3).abs()]!;
    final Mood color = rating == 0
        ? Mood.neutral
        : rating > 0
            ? Mood.positive
            : Mood.negative;

    return IconDefinition(glyph, color);
  }
}
