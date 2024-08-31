import 'package:shared_preferences/shared_preferences.dart';
import 'package:teufelsturm_viewer/utils/enum_extensions.dart';

class SharedPreferencesManager {
  static SharedPreferencesManager? _sharedPreferencesManager;  
  static SharedPreferences? _prefs;

  SharedPreferencesManager._createInstance();

  factory SharedPreferencesManager() {
    _sharedPreferencesManager ??= SharedPreferencesManager._createInstance();
    
    return _sharedPreferencesManager!;
  }  

  Future<SharedPreferences?> get prefs async {
    _prefs ??= await SharedPreferences.getInstance();    

    return _prefs;
  }

  Future<bool> setInt(String key, int value) async {
    SharedPreferences? preferences = await prefs; 
    return await preferences!.setInt(key, value);
  }

  Future<bool> setBool(String key, bool value) async {
    SharedPreferences? preferences = await prefs; 
    return await preferences!.setBool(key, value);
  }

  Future<bool> setDouble(String key, double value) async {
    SharedPreferences? preferences = await prefs; 
    return await preferences!.setDouble(key, value);
  }

  Future<bool> setString(String key, String value) async {
    SharedPreferences? preferences = await prefs; 
    return await preferences!.setString(key, value);
  }

  Future<bool> setStringList(String key, List<String> value) async {
    SharedPreferences? preferences = await prefs; 
    return await preferences!.setStringList(key, value);
  }

  Future<bool> setEnum(String key, Enum value) async {
    SharedPreferences? preferences = await prefs; 
    return await preferences!.setString(key, 
                                        EnumExtensions.enumToString(value));
  }

  Future<int?> getInt(String key) async {
    SharedPreferences? preferences = await prefs; 
    return preferences!.getInt(key);
  }

  Future<bool?> getBool(String key) async {
    SharedPreferences? preferences = await prefs; 
    return preferences!.getBool(key);
  }

  Future<double?> getDouble(String key) async {
    SharedPreferences? preferences = await prefs; 
    return preferences!.getDouble(key);
  }

  Future<String?> getString(String key) async {
    SharedPreferences? preferences = await prefs; 
    return preferences!.getString(key);
  }

  Future<List<String>?> getStringList(String key) async {
    SharedPreferences? preferences = await prefs; 
    return preferences!.getStringList(key);
  }    

  Future<T?> getEnum<T extends Enum>(String key, List<T> values) async {
  SharedPreferences preferences = await SharedPreferences.getInstance();
  var value = preferences.getString(key);
  return value == null ?
         null :
         EnumExtensions.tryStringToEnum<T>(value, values);
}
}