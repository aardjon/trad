///
/// Definition of the boundary between the core and the user interface.
///
library;

import '../entities/knowledgebase.dart';
import '../entities/post.dart';
import '../entities/route.dart';
import '../entities/sorting/posts_filter_mode.dart';
import '../entities/sorting/routes_filter_mode.dart';
import '../entities/summit.dart';

/// Interface providing user interactions to the core.
///
/// This is the application-wide access point for user interactions.
abstract interface class PresentationBoundary {
  /// Initializes the user interface.
  ///
  /// This may display some kind of "loading" or "splash" screen if appropriate.
  void initUserInterface();

  /// Let the UI display the list of summits in the *route db* domain.
  ///
  /// The actual summit list data must be set separately by calling [updateSummitList()].
  void showSummitList();

  /// Notify the user interface about a new (e.g. filtered) summit list.
  ///
  /// The current display may be updated with the provided [summitList], if necessary.
  void updateSummitList(List<Summit> summitList);

  /// Let the UI display details about the [selectedSummit] in the *route db* domain.
  ///
  /// The list of routes onto this summit must be set separately and can also be changed afterwards
  /// by calling [updateRouteList].
  void showSummitDetails(Summit selectedSummit);

  /// Notify the user interface about a new (e.g. filtered) route list.
  ///
  /// The current display may be updated with the provided [routeList], if necessary.
  /// [usedSortCriterion] defines the sort criterion the [routeList] is ordered by.
  void updateRouteList(List<Route> routeList, RoutesFilterMode usedSortCriterion);

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

  /// Change the active domain to the *About* domain.
  void switchToAbout();
}
