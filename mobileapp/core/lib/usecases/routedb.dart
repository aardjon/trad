///
/// Definition of the RouteDbUseCases use case class.
///
library;

import 'dart:async';

import 'package:crosscuttings/di.dart';
import 'package:crosscuttings/logging/logger.dart';

import '../boundaries/ota.dart';
import '../boundaries/presentation.dart';
import '../boundaries/storage/preferences.dart';
import '../boundaries/storage/routedb.dart';
import '../boundaries/sysenv.dart';
import '../entities/data_source.dart';
import '../entities/errors.dart';
import '../entities/post.dart';
import '../entities/route.dart';
import '../entities/sorting/posts_filter_mode.dart';
import '../entities/sorting/routes_filter_mode.dart';
import '../entities/summit.dart';

/// Logger to be used in this library file.
final Logger _logger = Logger('trad.core.usecases.routedb');

/// Use cases of the routedb domain.
class RouteDbUseCases {
  /// Interface to the presentation boundary component, used for displaying things.
  final PresentationBoundary _presentationBoundary;

  /// Interface to the storage boundary component, used for loading stored data.
  final RouteDbStorageBoundary _storageBoundary;

  /// Interface to the download boundary, used for fetching database updates.
  final RouteDbDownloadBoundary _downloadBoundary;

  /// Interface to the storage boundary component, used for reading and writing application config
  /// settings.
  final AppPreferencesBoundary _preferencesBoundary;

  /// Interface to the operating system environment.
  final SystemEnvironmentBoundary _systemEnvBoundary;

  /// Constructor for creating a new RouteDbUseCases instance.
  RouteDbUseCases(DependencyProvider di)
    : _presentationBoundary = di.provide<PresentationBoundary>(),
      _storageBoundary = di.provide<RouteDbStorageBoundary>(),
      _downloadBoundary = di.provide<RouteDbDownloadBoundary>(),
      _preferencesBoundary = di.provide<AppPreferencesBoundary>(),
      _systemEnvBoundary = di.provide<SystemEnvironmentBoundary>();

  /// Use case: Download the most current route database via OTA and install (import) it.
  Future<void> updateRouteDatabase() async {
    _logger.debug('Running use case updateRouteDatabase()');
    _presentationBoundary.routeDbUpdateTaskStarted();
    DateTime? dbCreationDate;

    if (_storageBoundary.isStarted()) {
      dbCreationDate = await _storageBoundary.getCreationDate();
    }
    await _fetchAndInstallRouteDb(
      dbFileProvider: OnlineDbFileProvider(_downloadBoundary, dbCreationDate),
    );
    _presentationBoundary.routeDbUpdateTaskDone();
    await _downloadBoundary.cleanupResources();
  }

  /// Use Case: Import the file given by [filePath] into the route db, replacing all previous data.
  Future<void> importRouteDbFile(String filePath) async {
    _logger.debug('Running use case importRouteDbFile()');
    await _fetchAndInstallRouteDb(
      dbFileProvider: LocalDbFileProvider(filePath),
    );
  }

  /// Fetch and install a new route db file. The actual work is delegated to to the given
  /// [dbFileProvider].
  Future<void> _fetchAndInstallRouteDb({
    required DbFileProvider dbFileProvider,
  }) async {
    if (_storageBoundary.isStarted()) {
      _storageBoundary.stopStorage();
      _presentationBoundary.updateRouteDbStatus(null, <DataSourceAttribution>[]);
    }

    String? filePath = await dbFileProvider.determineLocalFileToInstall();
    if (filePath != null) {
      try {
        await _storageBoundary.importRouteDbFile(filePath);
      } on Exception catch (error, stackTrace) {
        _logger.warning('Unable to import database file due to', error, stackTrace);
        // TODO(aardjon): Request the UI to show an error
      }
    }

    // TODO(aardjon): This is a code duplication with the startApplication() use case, eliminate!
    try {
      // Start again with the installed database. If the import failed, this is the previous one.
      await _storageBoundary.startStorage();
      DateTime routeDbDate = await _storageBoundary.getCreationDate();
      List<DataSourceAttribution> dataSources = await _storageBoundary.getExternalDataSources();
      _presentationBoundary.updateRouteDbStatus(routeDbDate, dataSources);
    } on StorageStartingException {
      // No or an invalid DB may have been there before already
      _presentationBoundary.updateRouteDbStatus(null, <DataSourceAttribution>[]);
    }
  }

  /// Use Case: Switch to the summit list, resetting any previous filter
  Future<void> showSummitListPage() async {
    _logger.info('Running use case showSummitListPage()');
    _presentationBoundary.updateSummitList(<Summit>[]);
    _presentationBoundary.showSummitList();
    List<Summit> summitList = await _storageBoundary.retrieveSummits();
    _presentationBoundary.updateSummitList(summitList);
  }

  /// Use Case: Update the summit list to show only the entries matching the given filter text.
  Future<void> filterSummitList(String filterText) async {
    _logger.info('Running use case filterSummitList($filterText)');
    List<Summit> summitList = await _storageBoundary.retrieveSummits(filterText);
    _presentationBoundary.updateSummitList(summitList);
  }

  /// Use Case: Show all routes for the selected summit.
  Future<void> showRouteListPage(int summitId) async {
    _logger.info('Running use case showRouteListPage($summitId)');
    RoutesFilterMode sortCriterion = await _preferencesBoundary.getInitialRoutesSortCriterion();
    Summit selectedSummit = await _storageBoundary.retrieveSummit(summitId);
    _presentationBoundary.showSummitDetails(selectedSummit);
    List<Route> routeList = await _storageBoundary.retrieveRoutesOfSummit(summitId, sortCriterion);
    _presentationBoundary.updateRouteList(routeList, sortCriterion);
  }

  /// Use Case: Sort the route list by a certain criterion
  Future<void> sortRouteList(int summitId, RoutesFilterMode sortCriterion) async {
    _logger.info('Running use case sortRouteList($summitId, $sortCriterion)');
    unawaited(_preferencesBoundary.setInitialRoutesSortCriterion(sortCriterion));
    List<Route> routeList = await _storageBoundary.retrieveRoutesOfSummit(summitId, sortCriterion);
    _presentationBoundary.updateRouteList(routeList, sortCriterion);
  }

  /// Use Case: Show/Open a certain Summit on a map
  Future<void> showSummitOnMap(int summitId) async {
    _logger.info('Running use case showSummitOnMap($summitId)');
    Summit selectedSummit = await _storageBoundary.retrieveSummit(summitId);
    if (selectedSummit.position != null) {
      await _systemEnvBoundary.openExternalMapsApp(selectedSummit.position!);
    } else {
      // Normally this shouldn't happen because the UI is not supposed to allow this use case for
      // summits without a geo position. So if it does, there is another error somewhere else. For
      // the same reason it's not necessary to show an explicit "error" use feedback - they
      // shouldn't be able to end up here at all.
      _logger.warning(
        "Summit '${selectedSummit.name}' (${selectedSummit.id}) doesn't have a position to display "
        'on a map, ignoring.',
      );
    }
  }

  /// Use Case: Show all posts for the selected route.
  Future<void> showPostsPage(int routeId) async {
    _logger.info('Running use case showPostsPage($routeId)');
    PostsFilterMode sortCriterion = await _preferencesBoundary.getInitialPostsSortCriterion();
    Route selectedRoute = await _storageBoundary.retrieveRoute(routeId);
    _presentationBoundary.showRouteDetails(selectedRoute);
    List<Post> postList = await _storageBoundary.retrievePostsOfRoute(routeId, sortCriterion);
    _presentationBoundary.updatePostList(postList, sortCriterion);
  }

  /// Use Case: Sort the post list by a certain criterion.
  Future<void> sortPostList(int routeId, PostsFilterMode sortCriterion) async {
    _logger.info('Running use case sortPostList($routeId, $sortCriterion)');
    unawaited(_preferencesBoundary.setInitialPostsSortCriterion(sortCriterion));
    List<Post> postList = await _storageBoundary.retrievePostsOfRoute(routeId, sortCriterion);
    _presentationBoundary.updatePostList(postList, sortCriterion);
  }
}

/// Interface for determining a local file that shall be installed as new route database.
abstract interface class DbFileProvider {
  /// Return the full path to the route database file to install. If there is no such file (e.g.
  /// because there are no updates at all), null is returned.
  Future<String?> determineLocalFileToInstall();
}

/// DbFileProvider implementation that simply provides the file path defined on construction.
class LocalDbFileProvider implements DbFileProvider {
  /// The full route database file path to provide.
  final String _filePath;

  /// Constructor for directly initializing all members.
  LocalDbFileProvider(this._filePath);

  @override
  Future<String?> determineLocalFileToInstall() async {
    return _filePath;
  }
}

/// DbFileProvider implementation that downloads the most current route database file from the OTA
/// service, and provides it.
class OnlineDbFileProvider implements DbFileProvider {
  /// Interface to the download boundary, used for fetching database updates.
  final RouteDbDownloadBoundary _downloadBoundary;

  /// Creation date of the database, if any. Used to ignore older candidates.
  final DateTime? _currentDbCreationDate;

  /// Constructor for directly initializing all members.
  OnlineDbFileProvider(this._downloadBoundary, this._currentDbCreationDate);

  @override
  Future<String?> determineLocalFileToInstall() async {
    List<RouteDbUpdateCandidate> availableDatabases = await _downloadBoundary
        .getAvailableUpdateCandidates();
    if (availableDatabases.isEmpty) {
      _logger.info('There are no compatible route databases available for download.');
      return null;
    }

    RouteDatabaseId? chosenUpdateId = await _chooseUpdateId(availableDatabases);
    if (chosenUpdateId == null) {
      _logger.info('No updated route database available.');
      return null;
    }

    _logger.info("Chose database '$chosenUpdateId' out of ${availableDatabases.length} candidates");
    return _downloadBoundary.downloadRouteDatabase(chosenUpdateId);
  }

  Future<RouteDatabaseId?> _chooseUpdateId(List<RouteDbUpdateCandidate> availableDatabases) async {
    // Use a "long ago" fallback if there is no current route DB to compare candidates against
    DateTime currentDbDate = _currentDbCreationDate ?? DateTime(1900);
    availableDatabases.sort(_compareUpdateCandidates);
    for (final RouteDbUpdateCandidate candidate in availableDatabases) {
      if (candidate.creationDate.isAfter(currentDbDate)) {
        return candidate.identifier;
      }
    }
    return null;
  }

  static int _compareUpdateCandidates(RouteDbUpdateCandidate left, RouteDbUpdateCandidate right) {
    // If two creation dates are different, the newest one shall be first
    int compareResult = right.creationDate.compareTo(left.creationDate);
    if (compareResult == 0) {
      // For equal creation dates, databases of a fully compatible format shall be preferred over
      // backward compatible ones
      if (left.compatibilityMode == CompatibilityMode.exactMatch &&
          right.compatibilityMode == CompatibilityMode.backwardCompatible) {
        compareResult = -1;
      } else if (left.compatibilityMode == CompatibilityMode.backwardCompatible &&
          right.compatibilityMode == CompatibilityMode.exactMatch) {
        compareResult = 1;
      }
    }
    return compareResult;
  }
}
