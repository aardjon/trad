///
/// Definition of the RouteDbUseCases use case class.
///
library;

import 'dart:async';

import 'package:crosscuttings/di.dart';
import 'package:crosscuttings/logging/logger.dart';

import '../boundaries/presentation.dart';
import '../boundaries/storage/preferences.dart';
import '../boundaries/storage/routedb.dart';
import '../boundaries/sysenv.dart';
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

  /// Interface to the storage boundary component, used for reading and writing application config
  /// settings.
  final AppPreferencesBoundary _preferencesBoundary;

  /// Interface to the operating system environment.
  final SystemEnvironmentBoundary _systemEnvBoundary;

  /// Factory function for creating the DbFileInstaller to use for actually installing a certain DB
  /// file. May be used to inject a mocked installer for easier unit testing.
  final DbFileInstaller Function(RouteDbStorageBoundary, PresentationBoundary) _createDbInstaller;

  /// Constructor for creating a new RouteDbUseCases instance.
  ///
  /// The [dbInstallerFactory] parameter allows unit tests to inject a user-defined or mocked
  /// DbFileInstaller and should not be given in normal production code.
  RouteDbUseCases(
    DependencyProvider di, {
    DbFileInstaller Function(RouteDbStorageBoundary, PresentationBoundary)? dbInstallerFactory,
  }) : _presentationBoundary = di.provide<PresentationBoundary>(),
       _storageBoundary = di.provide<RouteDbStorageBoundary>(),
       _preferencesBoundary = di.provide<AppPreferencesBoundary>(),
       _systemEnvBoundary = di.provide<SystemEnvironmentBoundary>(),
       _createDbInstaller = dbInstallerFactory ?? LocalDbFileInstaller.new;

  /// Use Case: Import the file given by [filePath] into the route db, replacing all previous data.
  Future<void> importRouteDbFile(String filePath) async {
    _logger.debug('Running use case importRouteDbFile()');

    await _fetchAndInstallRouteDb(
      dbFileProvider: LocalDbFileProvider(filePath),
      dbFileInstaller: _createDbInstaller(_storageBoundary, _presentationBoundary),
    );
  }

  /// Fetch and install a new route db file. The actual work is delegated to to the given
  /// [dbFileProvider] and [dbFileInstaller].
  Future<void> _fetchAndInstallRouteDb({
    required DbFileProvider dbFileProvider,
    required DbFileInstaller dbFileInstaller,
  }) async {
    String? filePath = await dbFileProvider.determineLocalFileToInstall();
    if (filePath != null) {
      await dbFileInstaller.installFromLocalFile(filePath);
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

/// Interface for actually installing a route database file.
abstract interface class DbFileInstaller {
  /// Install the file form the the given [filePath] as new route database. The previous database
  /// (if any) is discarded if the installation was successful. In case of an error, the previous
  /// database file is kept.
  Future<void> installFromLocalFile(String filePath);
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

/// DbFileInstaller implementation for installing a local database file. This is the normal
/// implementation used in production code.
class LocalDbFileInstaller implements DbFileInstaller {
  /// Interface to the storage boundary component, used for loading stored data.
  final RouteDbStorageBoundary _storageBoundary;

  /// Interface to the presentation boundary component, used for displaying things.
  final PresentationBoundary _presentationBoundary;

  /// Constructor for directly initializing all members.
  LocalDbFileInstaller(this._storageBoundary, this._presentationBoundary);

  @override
  Future<void> installFromLocalFile(String filePath) async {
    if (_storageBoundary.isStarted()) {
      _storageBoundary.stopStorage();
    }
    try {
      await _storageBoundary.importRouteDbFile(filePath);
    } on Exception catch (error, stackTrace) {
      _logger.warning('Unable to import database file due to', error, stackTrace);
      // TODO(aardjon): Request the UI to show an error
    }

    // TODO(aardjon): This is a code duplication with the startApplication() use case, eliminate!
    try {
      // Start again with the installed database. If the import failed, this is the previous one.
      await _storageBoundary.startStorage();
      DateTime routeDbDate = await _storageBoundary.getCreationDate();
      _presentationBoundary.updateRouteDbStatus(routeDbDate);
    } on StorageStartingException {
      // No or an invalid DB may have been there before already
      _presentationBoundary.updateRouteDbStatus(null);
    }
  }
}
