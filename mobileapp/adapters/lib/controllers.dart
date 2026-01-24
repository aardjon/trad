///
/// Provides controller implementations.
///
/// Controllers connect the concrete UI implementation to the `core` (in this direction) and are
/// basically responsible for mapping UI messages to use cases, converting data as necessary.
///
/// In a way, Controllers are the counterpart of Presenters.
///
library;

import 'dart:async';

import 'package:core/entities/sorting/posts_filter_mode.dart';
import 'package:core/entities/sorting/routes_filter_mode.dart';
import 'package:core/usecases/appwide.dart';
import 'package:core/usecases/knowledgebase.dart';
import 'package:core/usecases/routedb.dart';
import 'package:crosscuttings/di.dart';
import 'package:crosscuttings/logging/logger.dart';

import 'boundaries/repositories/assets.dart';
import 'boundaries/ui.dart';

/// Logger to be used in this library file.
final Logger _logger = Logger('trad.adapters.controllers');

/// Controller for transmitting UI messages to the core.
///
/// This is the general, application-wide controller. Domain specific use cases are separated into
/// more specialized classes.
class ApplicationWideController {
  /// The use case object from the `core` ring.
  final ApplicationWideUseCases _globalUsecases = ApplicationWideUseCases(DependencyProvider());

  final KnowledgebaseUseCases _knowledgebaseUsecases = KnowledgebaseUseCases(DependencyProvider());

  final RouteDbUseCases _routeDbUseCases = RouteDbUseCases(DependencyProvider());

  /// The user requested a switch to the Journal domain.
  void requestSwitchToJournal() {
    _globalUsecases.switchToJournal();
  }

  /// The user requested a switch to the knowledge base domain.
  void requestSwitchToKnowledgebase() {
    unawaited(_knowledgebaseUsecases.showHomePage());
  }

  /// The user requested a switch to the Route DB domain.
  void requestSwitchToRouteDb() {
    unawaited(_routeDbUseCases.showSummitListPage());
  }

  /// The user requested a switch to the Settings domain.
  void requestSwitchToSettings() {
    _globalUsecases.switchToSettings();
  }
}

/// Controller for transmitting knowledge base UI messages to the core.
class KnowledgebaseController {
  /// The use case object from the `core` ring.
  final KnowledgebaseUseCases _knowledgebaseUsecases = KnowledgebaseUseCases(DependencyProvider());

  /// The user requested to display the document with ID [documentId].
  void requestShowDocument(AssetId documentId) {
    _logger.debug('UI request: Show knowledgebase document $documentId');
    unawaited(_knowledgebaseUsecases.showDocumentPage(documentId));
  }
}

/// Controller for transmitting route DB UI messages to the core.
class RouteDbController {
  /// The use case object from the `core` ring.
  final RouteDbUseCases _routeDbUseCases = RouteDbUseCases(DependencyProvider());

  /// The user requested updating the route database.
  void requestRouteDbUpdate() {
    _logger.debug('UI request: Update route database');
    unawaited(_routeDbUseCases.updateRouteDatabase());
  }

  /// The user selected the route database file [selectedDbFile] to be imported.
  void requestRouteDbFileImport(String selectedDbFile) {
    _logger.debug('UI request: Import route DB file "$selectedDbFile"');
    unawaited(_routeDbUseCases.importRouteDbFile(selectedDbFile));
  }

  /// The user requested to filter the summit list by [filterText].
  void requestFilterSummitList(String filterText) {
    _logger.debug('UI request: Filter summit list for "$filterText"');
    unawaited(_routeDbUseCases.filterSummitList(filterText));
  }

  /// The user requested to see all details of the single summit identified by [summitDataId].
  void requestSummitDetails(ItemDataId summitDataId) {
    _logger.debug('UI request: Show details for summit with ID $summitDataId');
    unawaited(_routeDbUseCases.showRouteListPage(summitDataId));
  }

  /// The user requested to sort all routes of the summit identified by [summitDataId] by the
  /// criterion identified by [sortMenuItemId].
  void requestRouteListSorting(ItemDataId summitDataId, ItemDataId sortMenuItemId) {
    _logger.debug('UI request: Sort route list of $summitDataId by $sortMenuItemId');
    unawaited(
      _routeDbUseCases.sortRouteList(summitDataId, RoutesFilterMode.values[sortMenuItemId]),
    );
  }

  /// The user requested to show the summit [summitDataId] on a map.
  void requestShowSummitOnMap(ItemDataId summitDataId) {
    _logger.debug('UI request: Show summit $summitDataId on map');
    unawaited(_routeDbUseCases.showSummitOnMap(summitDataId));
  }

  /// The user requested to see all details of the single route identified by [routeDataId].
  void requestRouteDetails(ItemDataId routeDataId) {
    _logger.debug('UI request: Show details for route with ID $routeDataId');
    unawaited(_routeDbUseCases.showPostsPage(routeDataId));
  }

  /// The user requested to sort all posts of the route identified by [routeDataId] by the
  /// criterion identified by [sortMenuItemId].
  void requestPostListSorting(ItemDataId routeDataId, ItemDataId sortMenuItemId) {
    _logger.debug('UI request: Sort post list of $routeDataId by $sortMenuItemId');
    unawaited(_routeDbUseCases.sortPostList(routeDataId, PostsFilterMode.values[sortMenuItemId]));
  }
}
