///
/// Provides presenter implementations.
///
/// Presenters connect the `core` to the concrete UI implementation (in this direction) and are
/// responsible for providing displayable data (i.e. "everything the user can see").
///
/// In a way, Presenters are the counterpart of Controllers.
///
library;

import 'package:crosscuttings/appmeta.dart';
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

  /// Creator for converting difficulty grades into display strings.
  final SaxonGradeLabelCreator _labelCreator = SaxonGradeLabelCreator();

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
        ListViewItem('Über trad', icon: const IconDefinition(Glyph.logoAppInfo)),
        '$applicationName Version $applicationVersion',
      ),
    );
  }

  @override
  void updateRouteDbStatus(DateTime? routeDatabaseDate) {
    const String noDbMessage =
        'Es liegen keine Wegedaten vor weshalb die Wegedatenbank deaktiviert wurde. Aktiviere sie, '
        'indem du Wegedaten herunterlädst bzw. importierst.';

    final DateFormat dateFormatter = DateFormat('dd.MM.yyyy HH:mm');

    final List<ListViewItem> dataSourceAttributions = <ListViewItem>[
      ListViewItem(
        'OpenStreetMap',
        subTitle: 'OSM-Mitwirkende (ODbL)',
        content: 'https://www.openstreetmap.org',
      ),
      ListViewItem('Teufelsturm', subTitle: 'Andreas Lein', content: 'https://teufelsturm.de'),
      ListViewItem(
        'Sandsteinklettern',
        subTitle: 'Jörg Brutscher',
        content: 'http://www.sandsteinklettern.de',
      ),
    ];

    ApplicationUiBoundary ui = _dependencyProvider.provide<ApplicationUiBoundary>();
    ui.updateRouteDbStatus(
      activated: routeDatabaseDate != null,
      label: routeDatabaseDate != null ? dateFormatter.format(routeDatabaseDate) : 'Keine',
      dataSourceAttributions: routeDatabaseDate != null ? dataSourceAttributions : <ListViewItem>[],
      statusMessage: routeDatabaseDate != null ? null : noDbMessage,
    );
  }

  @override
  void routeDbUpdateTaskStarted() {
    ApplicationUiBoundary ui = _dependencyProvider.provide<ApplicationUiBoundary>();
    ui.updateRouteDbUpdateProgress(inProgress: true);
  }

  @override
  void routeDbUpdateTaskDone() {
    ApplicationUiBoundary ui = _dependencyProvider.provide<ApplicationUiBoundary>();
    ui.updateRouteDbUpdateProgress(inProgress: false);
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
          subTitle: _labelCreator.createGradeLabel(route),
          endIcon: route.routeRating != null
              ? _ratingMapper.getDoubleRatingIcon(route.routeRating!)
              : null,
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
      _labelCreator.createGradeLabel(selectedRoute),
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
      routeDbSectionTitle: 'Wegedaten',
      routeDbIdLabel: 'Datenstand:',
      routeDbUpdateLabel: 'Wegedaten herunterladen',
      routeDbFileSelectionActionLabel: 'Wegedaten aus Datei importieren',
      routeDbFileSelectionFieldLabel: 'Bitte eine Wegedatenbankdatei zum Importieren auswählen',
      routeDbUpdateInProgressLabel: 'Wegedaten werden heruntergeladen...',
    );
    ApplicationUiBoundary ui = _dependencyProvider.provide<ApplicationUiBoundary>();
    ui.showSettings(settingsModel);
  }

  @override
  void showAppInfo() {
    AppInfoModel aboutModel = AppInfoModel(
      pageTitle: 'Über trad',
      versionLabel: 'Du verwendest $applicationName in Version $applicationVersion',
      copyrightAttributionLabels: <String>[
        '© Karsten & Thomas Wesenigk',
        'Lizensiert unter der EUPL 1.2',
      ],
      websiteButtonLabel: 'Website aufrufen',
      routeDataHeader: 'Wegedaten',
      routeDataSourcesLabel:
          'Die heruntergeladenen Gipfel- und Wegeinformationen stammen aus den folgenden Quellen:',
      routeDataDisclaimer: 'Die Inhalte können veraltet, unvollständig oder falsch sein!',
      noRouteDataMessage: 'Momentan liegen keine Wegedaten vor.',
      supportHeader: 'Unterstützen',
      supportLabels: <String>[
        'Wir freuen uns über Fehlerhinweise und Verbesserungsvorschläge zu dieser App.',
        'Kontaktmöglichkeiten findest du auf unserer Website.',
        'Bitte hilf auch gern mit, die verwendeten Datenquellen zu verbessern oder zu erweitern.',
      ],
    );
    ApplicationUiBoundary ui = _dependencyProvider.provide<ApplicationUiBoundary>();
    ui.showAppInfo(aboutModel);
  }
}

/// Creates difficulty labels ("grade labels") for routes. Separated from the Presenter to simplify
/// testing, and to allow easier future extension in case we ever need other grade systems.
class SaxonGradeLabelCreator {
  /// Return a string describing the difficulty rating for the given [route].
  String createGradeLabel(Route route) {
    Difficulty difficulty = route.grade;

    List<String> labels = <String>[];

    if (route.dangerous) {
      labels.add('!');
    }
    if (route.stars > 0) {
      labels.add('*' * route.stars);
    }

    if (difficulty.jump > Difficulty.noGrade && difficulty.af > Difficulty.noGrade) {
      labels.add('${_jumpGradeToString(difficulty.jump)}/${_climbingGradeToString(difficulty.af)}');
    } else if (difficulty.jump > Difficulty.noGrade) {
      labels.add(_jumpGradeToString(difficulty.jump));
    } else if (difficulty.af > Difficulty.noGrade) {
      labels.add(_climbingGradeToString(difficulty.af));
    }

    if (route.grade.ou > Difficulty.noGrade) {
      labels.add('(${_climbingGradeToString(route.grade.ou)})');
    }
    if (route.grade.rp > Difficulty.noGrade) {
      labels.add('RP ${_climbingGradeToString(route.grade.rp)}');
    }

    return labels.join(' ');
  }

  String _jumpGradeToString(int grade) {
    // Only meant to be used for valid grades, i.e. positive, non-null, <10
    return '$grade';
  }

  String _climbingGradeToString(int grade) {
    if (grade == Difficulty.noGrade) {
      throw ArgumentError('Cannot create a string for "no grade" value');
    }
    if (grade < 7) {
      const List<String> romanNumbers = <String>['I', 'II', 'III', 'IV', 'V', 'VI'];
      return romanNumbers[grade - 1];
    }
    const List<String> romanNumbers = <String>[
      'VII',
      'VIII',
      'IX',
      'X',
      'XI',
      'XII',
      'XIII',
      'XIV',
    ];
    const List<String> subGrades = <String>['a', 'b', 'c'];
    String major = romanNumbers[((grade - 7) ~/ 3)];
    String minor = subGrades[(grade - 1) % 3];
    return '$major$minor';
  }
}
