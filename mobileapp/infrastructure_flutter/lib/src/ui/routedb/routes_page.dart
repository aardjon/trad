import 'package:flutter/material.dart';
import 'package:loading_indicator/loading_indicator.dart';
import 'package:teufelsturm_viewer/models/peak_data.dart';
import 'package:teufelsturm_viewer/models/route_data.dart';
import 'package:teufelsturm_viewer/pages/posts_page.dart';
import 'package:teufelsturm_viewer/utils/rating_helper.dart';
import 'package:teufelsturm_viewer/utils/routes_filter_mode.dart';
import 'package:teufelsturm_viewer/utils/shared_preferences_manager.dart';
import 'package:teufelsturm_viewer/utils/sqlite_manager.dart';

class RoutesPage extends StatefulWidget {
  final PeakData peak;
  final SqliteManager sqliteManager;

  const RoutesPage({required this.peak, required this.sqliteManager, super.key});

  @override
  State<RoutesPage> createState() => _RoutesPageState();
}

class _RoutesPageState extends State<RoutesPage> {
  List<RouteData> _routes = <RouteData>[];
  bool _routesLoaded = false;
  final SharedPreferencesManager _sharedPreferencesManager = SharedPreferencesManager();
  RoutesFilterMode _routesFilterMode = RoutesFilterMode.name;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: _appBar(),
      body: _routesLoaded ? _listView() : _showLoadingIndicator(),
    );
  }

  @override
  void dispose() {
    super.dispose();
  }

  @override
  void initState() {
    super.initState();

    Future.wait(<Future<void>>[_loadRoutesFilterMode(), _loadRoutesFromDatabase()]).then((_) {
      _sortRoutes();
    });
  }

  AppBar _appBar() {
    return AppBar(
      title: Text(widget.peak.peakName),
      centerTitle: true,
      backgroundColor: Colors.lightGreen,
      actions: <Widget>[
        IconButton(
          onPressed: _showFilterOptions,
          icon: const Icon(Icons.filter_list),
        ),
      ],
    );
  }

  ListTile _createFilterMenuItem(
    BuildContext context,
    RoutesFilterMode routesFilterMode,
    String title,
  ) {
    return ListTile(
      title: Text(title),
      trailing: _routesFilterMode == routesFilterMode ? const Icon(Icons.done) : const Icon(null),
      onTap: () {
        _setFilter(routesFilterMode);
        Navigator.pop(context);
      },
    );
  }

  ListView _listView() {
    return ListView.builder(
      itemCount: _routes.length,
      itemBuilder: (BuildContext context, int index) {
        String routeName = _routes[index].routeName;
        String routeGrade = _routes[index].routeGrade;
        double? routeRating = _routes[index].routeRating;

        return ListTile(
          title: Text(routeName),
          subtitle: Text(routeGrade),
          trailing: RatingHelper.getDoubleRatingIcon(routeRating),
          onTap: () {
            Navigator.push(
              context,
              MaterialPageRoute(
                builder: (BuildContext context) => PostsPage(
                  route: _routes[index],
                  sqliteManager: widget.sqliteManager,
                ),
              ),
            );
          },
        );
      },
    );
  }

  Future<void> _loadRoutesFilterMode() async {
    _routesFilterMode = await _sharedPreferencesManager.getEnum<RoutesFilterMode>(
          'routesFilterMode',
          RoutesFilterMode.values,
        ) ??
        _routesFilterMode;
  }

  Future<void> _loadRoutesFromDatabase() async {
    List<RouteData> routes = await widget.sqliteManager.getAllRoutes(
      widget.peak.id,
    );
    _routes = routes;
    _routesLoaded = true;
  }

  Future<bool> _saveRoutesFilterMode() async {
    return await _sharedPreferencesManager.setEnum(
      'routesFilterMode',
      _routesFilterMode,
    );
  }

  void _setFilter(RoutesFilterMode routesFilterMode) {
    _routesFilterMode = routesFilterMode;
    _saveRoutesFilterMode();
    _sortRoutes();
  }

  void _showFilterOptions() {
    showModalBottomSheet(
      context: context,
      builder: (BuildContext context) {
        return Column(
          mainAxisSize: MainAxisSize.min,
          children: <Widget>[
            _createFilterMenuItem(context, RoutesFilterMode.name, 'Name'),
            _createFilterMenuItem(context, RoutesFilterMode.grade, 'Schwierigkeitsgrad'),
            _createFilterMenuItem(context, RoutesFilterMode.rating, 'Bewertung'),
          ],
        );
      },
    );
  }

  LoadingIndicator _showLoadingIndicator() {
    return const LoadingIndicator(
      indicatorType: Indicator.ballClipRotateMultiple,
      colors: <Color>[Colors.lightGreen],
    );
  }

  void _sortRoutes() {
    final Map<RoutesFilterMode, Function> sortFunction = <RoutesFilterMode, Function>{
      RoutesFilterMode.name: () => _routes.sortByRouteName(),
      RoutesFilterMode.grade: () => _routes.sortByRouteGrade(),
      RoutesFilterMode.rating: () => _routes.sortByRouteRating(),
    };

    setState(() {
      sortFunction[_routesFilterMode]?.call();
    });
  }
}
