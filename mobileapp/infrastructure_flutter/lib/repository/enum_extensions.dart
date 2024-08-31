class EnumExtensions {
  static String enumToString(Enum value) {
    return value.name.toString();
  }

  static T? tryStringToEnum<T extends Enum>(String value, List<T> enumValues) {
    try {
      return enumValues.byName(value);
    } catch (e) {
      return null;
    }
  }
}
