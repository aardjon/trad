///
/// Unit tests for the adapters.presenters library.
///
library;

import 'package:adapters/boundaries/ui.dart';
import 'package:adapters/presenters.dart';
import 'package:core/entities/geoposition.dart';
import 'package:core/entities/route.dart';
import 'package:core/entities/summit.dart';
import 'package:crosscuttings/di.dart';
import 'package:mocktail/mocktail.dart';
import 'package:test/test.dart';

class FakeApplicationUi extends Mock implements ApplicationUiBoundary {}

/// Unit tests for the adapters.presenters.ApplicationWidePresenter class.
void main() {
  setUpAll(() {
    // Register a default values that are used by mocktails `any` matcher
    //registerFallbackValue(Query.table('example_table', <String>['example_column']));
    registerFallbackValue(
      MainMenuModel(
        '[NoTitle]',
        ListViewItem('[NoJournal]'),
        ListViewItem('[NoRouteDB]'),
        ListViewItem('[NoKnowledgebase]'),
        ListViewItem('[NoSettings]'),
        'Application version 0.0.0',
      ),
    );
    registerFallbackValue(SummitListModel('[NoPageTitle]', '[NoSearchBarHint]'));
    registerFallbackValue(SummitDetailsModel(0xFFFFFF, '[NoPageTitle]', canShowOnMap: false));
    registerFallbackValue(RouteDetailsModel(0xFFFFFF, '[NoPageTitle]', '[NoPageSubTitle]'));
    registerFallbackValue(
      SettingsModel(
        pageTitle: '[NoPageTitle]',
        routeDbIdLabel: '[NoRouteDbId]',
        routeDbUpdateLabel: '[NoRouteDbUpdateLabel]',
        routeDbFileSelectionActionLabel: '[NoFileSelectionActionLabel]',
        routeDbFileSelectionFieldLabel: '[NoFileSelectionFieldLabel]',
      ),
    );
  });

  FakeApplicationUi fakeUi = FakeApplicationUi();

  final DependencyProvider di = DependencyProvider();
  di.registerSingleton<ApplicationUiBoundary>(() => fakeUi);

  tearDown(() {
    // Reset the mocks after each test case
    reset(fakeUi);
  });

  /// Ensure the correct behaviour of the initUserInterface() method, i.e. send the expected static
  /// data to the actual UI implementation:
  ///  - The app name and the menu header must be equal (and be the expected string)
  ///  - A splash message must be set and contain the '...' string
  ///  - All main menu items must provide a (non-empty) text and an icon
  test('initUserInterface()', () {
    const String expectedAppName = 'Sandsteinklettern in Sachsen';
    ApplicationWidePresenter presenter = ApplicationWidePresenter();
    presenter.initUserInterface();

    // Configure a complex Matcher that checks the MainMenuModel object that the test expects to be
    // provided to the UI boundary (initializeUserInterface())
    Matcher menuModelMatcher = isA<MainMenuModel>()
        .having((MainMenuModel m) => m.menuHeader, 'menuHeader', equals(expectedAppName))
        .having((MainMenuModel m) => m.journalItem.mainTitle, 'journal.title', isNotEmpty)
        .having((MainMenuModel m) => m.journalItem.icon, 'journal.icon', isNotNull)
        .having(
          (MainMenuModel m) => m.knowledgebaseItem.mainTitle,
          'knowledgebase.title',
          isNotEmpty,
        )
        .having((MainMenuModel m) => m.knowledgebaseItem.icon, 'knowledgebase.icon', isNotNull)
        .having((MainMenuModel m) => m.routedbItem.mainTitle, 'routedb.title', isNotEmpty)
        .having((MainMenuModel m) => m.routedbItem.icon, 'routedb.icon', isNotNull)
        .having((MainMenuModel m) => m.settingsItem.mainTitle, 'settings.title', isNotEmpty)
        .having((MainMenuModel m) => m.settingsItem.icon, 'settings.icon', isNotNull);

    verify(
      () => fakeUi.initializeUserInterface(
        expectedAppName, // App Title
        any(that: contains('...')), // Splash Message
        any(that: menuModelMatcher),
      ),
    ).called(1);
  });

  group('routedb domain', () {
    /// Ensure the correct behaviour of the updateRouteDbStatus() method:
    ///  - If it gets a DB creation date, activate the routeDB domain in the UI, send the DB
    ///    creation date as part of the label and don't send a status message.
    ///  - If it gets null, deactivate the routeDB domain in the UI, send a special "No DB available"
    ///    label and send a status message.
    group('updateRouteDbStatus()', () {
      List<(DateTime?, bool)> testData = <(DateTime?, bool)>[
        (DateTime.now(), true),
        (null, false),
      ];
      for (final (DateTime?, bool) testParams in testData) {
        DateTime? dbCreationDT = testParams.$1;
        bool expectActivation = testParams.$2;
        test('$dbCreationDT', () {
          const String expectedMissingDbLabel = 'Keine';

          ApplicationWidePresenter presenter = ApplicationWidePresenter();
          presenter.updateRouteDbStatus(dbCreationDT);

          // Configure two  matchers for the parameters that we expect to be provided to the UI boundary.
          final Matcher dbLabelMatcher = expectActivation
              ? predicate(
                  (String label) =>
                      label != expectedMissingDbLabel &&
                      label.contains(dbCreationDT!.toIso8601String()),
                )
              : equals(expectedMissingDbLabel);
          final Matcher availabilityMessageMatcher = expectActivation ? isNull : isNotEmpty;

          verify(
            () => fakeUi.updateRouteDbStatus(
              activated: expectActivation,
              label: any(named: 'label', that: dbLabelMatcher),
              statusMessage: any(named: 'statusMessage', that: availabilityMessageMatcher),
            ),
          ).called(1);
        });
      }
    });

    /// Ensure the expected behaviour of the showSummitList() method, i.e. send the expected static
    /// data to the actual UI implementation: Page title and search box label must not be empty.
    test('showSummitList()', () {
      ApplicationWidePresenter presenter = ApplicationWidePresenter();
      presenter.showSummitList();

      Matcher summitModelMatcher = isA<SummitListModel>()
          .having((SummitListModel m) => m.pageTitle, 'pageTitle', isNotEmpty)
          .having((SummitListModel m) => m.searchBarHint, 'searchBarHinter', isNotEmpty);
      verify(() => fakeUi.showSummitList(any(that: summitModelMatcher))).called(1);
    });

    /// Ensure the expected behaviour of the showSummitDetails() method, i.e. send the expected summit
    /// data to the actual UI implementation:
    ///  - Page title and data ID must be set correctly
    ///  - (Only) if a GeoPosition is available, the 'showOnMap'  flag must be set
    group('showSummitDetails()', () {
      List<(GeoPosition?, bool)> testData = <(GeoPosition?, bool)>[
        (GeoPosition(13.37, 47.11), true),
        (null, false),
      ];
      for (final (GeoPosition?, bool) testParams in testData) {
        GeoPosition? summitPosition = testParams.$1;
        bool expectMap = testParams.$2;

        test(summitPosition.toString(), () {
          ApplicationWidePresenter presenter = ApplicationWidePresenter();
          Summit summit = Summit(42, 'Mount Mock', summitPosition);
          presenter.showSummitDetails(summit);

          Matcher summitModelMatcher = isA<SummitDetailsModel>()
              .having((SummitDetailsModel m) => m.pageTitle, 'pageTitle', equals(summit.name))
              .having((SummitDetailsModel m) => m.summitDataId, 'dataID', equals(summit.id))
              .having((SummitDetailsModel m) => m.canShowOnMap, 'canShowOnMap', equals(expectMap));
          verify(() => fakeUi.showSummitDetails(any(that: summitModelMatcher))).called(1);
        });
      }
    });

    /// Ensure the expected behaviour of the showRouteDetails() method, i.e. send the expected static
    /// data to the actual UI implementation: Page (sub) title and data ID must be set correctly.
    test('showRouteDetails()', () {
      ApplicationWidePresenter presenter = ApplicationWidePresenter();
      Route selectedRoute = Route(42, 'Via Exempli', 'V', 2.4);
      presenter.showRouteDetails(selectedRoute);

      Matcher routeModelMatcher = isA<RouteDetailsModel>()
          .having((RouteDetailsModel m) => m.routeDataId, 'dataID', selectedRoute.id)
          .having((RouteDetailsModel m) => m.pageTitle, 'pageTitle', selectedRoute.routeName)
          .having(
            (RouteDetailsModel m) => m.pageSubTitle,
            'pageSubTitle',
            selectedRoute.routeGrade,
          );
      verify(() => fakeUi.showRouteDetails(any(that: routeModelMatcher))).called(1);
    });
  });

  /// Ensure the correct behaviour of the showSettings() method, i.e. send the expected static data
  /// to the actual UI implementation: Page title and all Labels must be set.
  test('showSettings()', () {
    ApplicationWidePresenter presenter = ApplicationWidePresenter();
    presenter.showSettings();

    Matcher settingsModelMatcher = isA<SettingsModel>()
        .having((SettingsModel m) => m.pageTitle, 'pageTitle', isNotEmpty)
        .having(
          (SettingsModel m) => m.routeDbFileSelectionActionLabel,
          'routeDbFileSelectionActionLabel',
          isNotEmpty,
        )
        .having(
          (SettingsModel m) => m.routeDbFileSelectionFieldLabel,
          'routeDbFileSelectionFieldLabel',
          isNotEmpty,
        )
        .having((SettingsModel m) => m.routeDbIdLabel, 'routeDbIdLabel', isNotEmpty);
    verify(() => fakeUi.showSettings(any(that: settingsModelMatcher))).called(1);
  });
}
