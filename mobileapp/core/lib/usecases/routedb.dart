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

  /// Constructor for creating a new RouteDbUseCases instance.
  RouteDbUseCases(DependencyProvider di)
    : _presentationBoundary = di.provide<PresentationBoundary>(),
      _storageBoundary = di.provide<RouteDbStorageBoundary>(),
      _preferencesBoundary = di.provide<AppPreferencesBoundary>();

  /// Use Case: Import the file given by [filePath] into the route db, replacing all previous data.
  Future<void> importRouteDbFile(String filePath) async {
    _logger.debug('Running use case importRouteDbFile()');
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
      // Start again with the default database. If the import failed, this is the previous one
      await _storageBoundary.startStorage();
      DateTime routeDbDate = await _storageBoundary.getCreationDate();
      _presentationBoundary.updateRouteDbStatus(routeDbDate);
    } on StorageStartingException {
      // No or an invalid DB may have been there before already
      _presentationBoundary.updateRouteDbStatus(null);
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
