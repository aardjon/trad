///
/// Definition of the Version class for storing version numbers.
///
library;

import 'package:meta/meta.dart';

/// Represents a two-component *semantic* version number.
///
/// See https://semver.org/ for more information about semantic versioning. This class differs from
/// the official definition by not providing the PATCH component.
///
/// Version numbers can be compared and ordered, earlier ("older") versions are considered "smaller"
/// than newer ones.
@immutable
class Version {
  /// The major part of a version number.
  ///
  /// This is incremented for incompatible changes. Must be an unsigned value.
  final int major;

  /// The minor part of a version number.
  ///
  /// This is incremented for backward-compatible changes. Must be an unsigned value.
  final int minor;

  /// Upper limit for the minor value.
  /// Minor values must be smaller than this limit. This is used to simplify hash calculation.
  static const int _minorNumberLimit = 1000;

  /// Constructor for directly initializing all members.
  Version(this.major, this.minor) {
    if (major < 0) {
      throw ArgumentError.value(major, 'Major version parts must not be negative values');
    }
    if (minor < 0) {
      throw ArgumentError.value(minor, 'Minor version parts must not be negative values');
    }
    if (minor >= _minorNumberLimit) {
      throw ArgumentError.value(
        minor,
        'Minor version parts must be smaller than $_minorNumberLimit',
      );
    }
  }

  /// Simple compatibility check for different versions.
  ///
  /// This checks if the given [other] version can be considered compatible to this one. This is the
  /// case if both versions are equal or if (only) the minor part of [other] is greater than this'
  /// minor part, which usually means that the entity described by [other] just provides some
  /// additional functionality. The compatibility check is *not* commutative.
  ///
  /// Returns true if the versions are compatible, otherwise false.
  bool isCompatible(Version other) {
    return major == other.major && minor >= other.minor;
  }

  @override
  String toString() {
    return '${super.toString()}: $major.$minor';
  }

  @override
  int get hashCode => major * _minorNumberLimit + minor;

  @override
  bool operator ==(Object other) {
    return other is Version && other.major == major && other.minor == minor;
  }

  /// Less than operator.
  /// Older versions are considered lower.
  bool operator <(Version other) {
    return major < other.major || (major == other.major && minor < other.minor);
  }

  /// Greater than operator.
  /// Newer versions are considered greater.
  bool operator >(Version other) {
    return major > other.major || (major == other.major && minor > other.minor);
  }

  /// Less or equal operator.
  /// Older versions are considered lower.
  bool operator <=(Version other) {
    return this == other || this < other;
  }

  /// Greater or equal operator.
  /// Newer versions are considered greater.
  bool operator >=(Version other) {
    return this == other || this > other;
  }
}
