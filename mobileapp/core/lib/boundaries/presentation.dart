///
/// Definition of the boundary between the core and the user interface.
///
library;

import '../entities/data_source.dart';
import '../entities/knowledgebase.dart';
import '../entities/post.dart';
import '../entities/route.dart';
import '../entities/sector.dart';
import '../entities/sorting/posts_filter_mode.dart';
import '../entities/sorting/routes_filter_mode.dart';
import '../entities/sorting/summits_filter_mode.dart';
import '../entities/summit.dart';

/// Interface providing user interactions to the core.
///
/// This is the application-wide access point for user interactions.
abstract interface class PresentationBoundary {
  /// Initializes the user interface.
  ///
  /// This may display some kind of "loading" or "splash" screen if appropriate.
  void initUserInterface();

  /// Notify the UI that a created at [routeDatabaseDate] from [dataSources] is now available.
  void routeDbAvailable(DateTime routeDatabaseDate, List<DataSourceAttribution> dataSources);

  /// Notify the UI that no route database is available (anymore).
  void routeDbUnavailable();

  /// Notify the UI about a running route database update.
  void routeDbUpdating();

  /// Notify the UI about an error that happened while updating.
  void routeDbUpdateError(Exception error);

  /// Let the UI display the list of summits in the *route db* domain.
  ///
  /// [sectors] is the list of sectors that may be selected for summit filtering. The actual summit
  /// list data must be set separately by calling [updateSummitList()].
  void showSummitList(List<Sector> sectors, int? selectedSectorId);

  /// Notify the user interface about a new (e.g. filtered or sorted) global summit list.
  ///
  /// The current display may be updated with the provided [summitList], if necessary.
  void updateSummitList(List<Summit> summitList);

  /// Let the UI display the list of nearby summits in the *route db* domain.
  ///
  /// The actual summit list data must be set separately by calling [updateNearbySummits()].
  void showNearbySummits();

  /// Notify the user interface about a new list of summits nearby the current position.
  ///
  /// The current display may be updated with the provided [nearbySummits], if necessary.
  void updateNearbySummits(List<(Summit, double)> nearbySummits);

  /// Let the UI display details about the [selectedSummit] in the *route db* domain.
  ///
  /// The list of routes onto this summit must be set separately and can also be changed afterwards
  /// by calling [updateRouteList].
  void showSummitDetails(Summit selectedSummit);

  /// Notify the user interface about a new (e.g. filtered or sorted) route list of the summit
  /// identified by [summitId].
  ///
  /// The current display may be updated with the provided [routeList], if necessary.
  /// [usedSortCriterion] defines the sort criterion the [routeList] is ordered by.
  void updateRouteList(int summitId, List<Route> routeList, RoutesFilterMode usedSortCriterion);

  /// Notify the user interface about a new (e.g. filtered or sorted) list of summits nearby the
  /// one identified by [summitId].
  ///
  /// The current display may be updated with the provided [nearbySummits], if necessary.
  void updateNearbySummitList(
    int summitId,
    List<(Summit, double)> nearbySummits,
    NearbySummitsSortMode usedSortCriterion,
  );

  /// Let the UI display details about the [selectedRoute] in the *route db* domain.
  ///
  /// The list of posts for this rout must be set separately and can also be changed afterwards by
  /// calling [updatePostList()].
  void showRouteDetails(Route selectedRoute);

  /// Notify the user interface about a new (e.g. filtered or reordered) post list.
  ///
  /// The current display may be updated with the provided [postList], if necessary.
  /// [usedSortCriterion] defines the sort criterion the [postList] is ordered by.
  void updatePostList(List<Post> postList, PostsFilterMode usedSortCriterion);

  /// Change the active domain to the *Journal* domain.
  void switchToJournal();

  /// Let the UI display the provided [document] in the *Knowledge base* domain.
  void showKnowledgebaseDocument(KnowledgebaseDocument document);

  /// Let the UI display the application settings (aka *settings* domain).
  void showSettings();

  /// Let the UI display the application information (aka *appinfo* domain).
  void showAppInfo();
}
