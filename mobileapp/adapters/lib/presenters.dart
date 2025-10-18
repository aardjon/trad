///
/// Provides presenter implementations.
///
/// Presenters connect the `core` to the concrete UI implementation (in this direction) and are
/// responsible for providing displayable data (i.e. "everything the user can see").
///
/// In a way, Presenters are the counterpart of Controllers.
///
library;

import 'package:intl/intl.dart';

import 'package:core/boundaries/presentation.dart';
import 'package:core/entities/knowledgebase.dart';
import 'package:core/entities/post.dart';
import 'package:core/entities/route.dart';
import 'package:core/entities/sorting/posts_filter_mode.dart';
import 'package:core/entities/sorting/routes_filter_mode.dart';
import 'package:core/entities/summit.dart';
import 'package:crosscuttings/di.dart';

import 'boundaries/ui.dart';
import 'src/ui/rating.dart';

/// Implementation of the application-wide presenter used by the core to interact with the user.
class ApplicationWidePresenter implements PresentationBoundary {
  /// DI instance for obtaining dependencies from other rings.
  final DependencyProvider _dependencyProvider = DependencyProvider();

  /// Mapper for getting the icon definitions describing certain ratings.
  static const RatingIconFactory _ratingMapper = RatingIconFactory();

  @override
  void initUserInterface() {
    const String appName = 'Sandsteinklettern in Sachsen';
    ApplicationUiBoundary ui = _dependencyProvider.provide<ApplicationUiBoundary>();
    ui.initializeUserInterface(
      appName,
      'Initialisierung läuft...',
      MainMenuModel(
        appName,
        ListViewItem('Fahrtenbuch', icon: const IconDefinition(Glyph.logoJournal)),
        ListViewItem('Wegedatenbank', icon: const IconDefinition(Glyph.logoRouteDb)),
        ListViewItem('Kletterlexikon', icon: const IconDefinition(Glyph.logoKnowledgeBase)),
        ListViewItem('Einstellungen', icon: const IconDefinition(Glyph.logoSettings)),
      ),
    );
  }

  @override
  void updateRouteDbStatus(DateTime? routeDatabaseDate) {
    const String noDbMessage =
        'Es liegen keine Wegedaten vor weshalb die Wegedatenbank deaktiviert wurde. Um sie zu '
        'aktivieren, importieren Sie bitte eine Wegedatenbankdatei.';

    ApplicationUiBoundary ui = _dependencyProvider.provide<ApplicationUiBoundary>();
    ui.updateRouteDbStatus(
      activated: routeDatabaseDate != null,
      label: routeDatabaseDate != null ? routeDatabaseDate.toIso8601String() : 'Keine',
      statusMessage: routeDatabaseDate != null ? null : noDbMessage,
    );
  }

  @override
  void showSummitList() {
    ApplicationUiBoundary ui = _dependencyProvider.provide<ApplicationUiBoundary>();
    SummitListModel model = SummitListModel('Gipfel', 'Gipfel suchen');
    ui.showSummitList(model);
  }

  @override
  void updateSummitList(List<Summit> summitList) {
    ApplicationUiBoundary ui = _dependencyProvider.provide<ApplicationUiBoundary>();
    List<ListViewItem> summitItems = <ListViewItem>[];
    for (final Summit summit in summitList) {
      summitItems.add(ListViewItem(summit.name, itemId: summit.id));
    }
    ui.updateSummitList(summitItems);
  }

  @override
  void showSummitDetails(Summit selectedSummit) {
    ApplicationUiBoundary ui = _dependencyProvider.provide<ApplicationUiBoundary>();
    SummitDetailsModel model = SummitDetailsModel(
      selectedSummit.id,
      selectedSummit.name,
      canShowOnMap: selectedSummit.position != null,
    );
    ui.showSummitDetails(model);
  }

  @override
  void updateRouteList(List<Route> routeList, RoutesFilterMode usedSortCriterion) {
    ApplicationUiBoundary ui = _dependencyProvider.provide<ApplicationUiBoundary>();
    List<ListViewItem> routeItems = <ListViewItem>[];
    for (final Route route in routeList) {
      routeItems.add(
        ListViewItem(
          route.routeName,
          subTitle: route.routeGrade,
          endIcon: _ratingMapper.getDoubleRatingIcon(route.routeRating ?? 0.0),
          itemId: route.id,
        ),
      );
    }
    ui.updateRouteList(routeItems, _createRoutesSortCriterionItems(usedSortCriterion));
  }

  List<ListViewItem> _createRoutesSortCriterionItems(RoutesFilterMode usedSortCriterion) {
    return <ListViewItem>[
      ListViewItem(
        'Name',
        endIcon: usedSortCriterion == RoutesFilterMode.name
            ? const IconDefinition(Glyph.checked)
            : null,
        itemId: RoutesFilterMode.name.index,
      ),
      ListViewItem(
        'Schwierigkeitsgrad',
        endIcon: usedSortCriterion == RoutesFilterMode.grade
            ? const IconDefinition(Glyph.checked)
            : null,
        itemId: RoutesFilterMode.grade.index,
      ),
      ListViewItem(
        'Bewertung',
        endIcon: usedSortCriterion == RoutesFilterMode.rating
            ? const IconDefinition(Glyph.checked)
            : null,
        itemId: RoutesFilterMode.rating.index,
      ),
    ];
  }

  @override
  void showRouteDetails(Route selectedRoute) {
    ApplicationUiBoundary ui = _dependencyProvider.provide<ApplicationUiBoundary>();
    RouteDetailsModel model = RouteDetailsModel(
      selectedRoute.id,
      selectedRoute.routeName,
      selectedRoute.routeGrade,
    );
    ui.showRouteDetails(model);
  }

  @override
  void updatePostList(List<Post> postList, PostsFilterMode usedSortCriterion) {
    ApplicationUiBoundary ui = _dependencyProvider.provide<ApplicationUiBoundary>();
    List<ListViewItem> postItems = <ListViewItem>[];
    for (final Post post in postList) {
      DateFormat formatter = DateFormat('dd.MM.yyyy HH:mm');
      String formattedDate = formatter.format(post.postDate);

      postItems.add(
        ListViewItem(
          post.userName,
          subTitle: formattedDate,
          content: post.comment,
          endIcon: _ratingMapper.getIntRatingIcon(post.rating),
        ),
      );
    }
    ui.updatePostList(postItems, _createPostsSortCriterionItems(usedSortCriterion));
  }

  List<ListViewItem> _createPostsSortCriterionItems(PostsFilterMode usedSortCriterion) {
    return <ListViewItem>[
      ListViewItem(
        'Neueste zuerst',
        endIcon: usedSortCriterion == PostsFilterMode.newestFirst
            ? const IconDefinition(Glyph.checked)
            : null,
        itemId: PostsFilterMode.newestFirst.index,
      ),
      ListViewItem(
        'Älteste zuerst',
        endIcon: usedSortCriterion == PostsFilterMode.oldestFirst
            ? const IconDefinition(Glyph.checked)
            : null,
        itemId: PostsFilterMode.oldestFirst.index,
      ),
    ];
  }

  @override
  void switchToJournal() {
    ApplicationUiBoundary ui = _dependencyProvider.provide<ApplicationUiBoundary>();
    ui.switchToJournal();
  }

  @override
  void showKnowledgebaseDocument(KnowledgebaseDocument document) {
    KnowledgebaseModel kbPageModel = KnowledgebaseModel(document.title, document.content);
    ApplicationUiBoundary ui = _dependencyProvider.provide<ApplicationUiBoundary>();
    ui.showKnowledgebase(kbPageModel);
  }

  @override
  void showSettings() {
    SettingsModel settingsModel = SettingsModel(
      pageTitle: 'Einstellungen',
      routeDbIdLabel: 'Aktuelle Wegedatenbank:',
      routeDbFileSelectionActionLabel: 'Wegedatenbank importieren',
      routeDbFileSelectionFieldLabel: 'Bitte eine Wegedatenbankdatei zum Importieren auswählen',
    );
    ApplicationUiBoundary ui = _dependencyProvider.provide<ApplicationUiBoundary>();
    ui.showSettings(settingsModel);
  }
}
