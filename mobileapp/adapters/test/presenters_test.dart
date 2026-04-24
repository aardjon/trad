///
/// Unit tests for the adapters.presenters library.
///
library;

import 'package:adapters/boundaries/ui.dart';
import 'package:adapters/presenters.dart';
import 'package:core/entities/data_source.dart';
import 'package:core/entities/geoposition.dart';
import 'package:core/entities/route.dart';
import 'package:core/entities/summit.dart';
import 'package:crosscuttings/di.dart';
import 'package:mocktail/mocktail.dart';
import 'package:test/test.dart';

class FakeApplicationUi extends Mock implements ApplicationUiBoundary {}

class FakeUi extends Fake implements ApplicationUiBoundary {
  String dbLabel = '';
  List<ListViewItem> dataSourceItems = <ListViewItem>[];

  @override
  void updateRouteDbStatus({
    required bool activated,
    required String label,
    required List<ListViewItem> dataSourceAttributions,
    String? statusMessage,
  }) {
    dbLabel = label;
    dataSourceItems = dataSourceAttributions;
  }
}

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
        ListViewItem('[NoAbout]'),
        'Application version 0.0.0',
      ),
    );
    registerFallbackValue(SummitListModel('[NoPageTitle]', '[NoSearchBarHint]'));
    registerFallbackValue(
      SummitDetailsModel(
        0xFFFFFF,
        '[NoPageTitle]',
        '[NoPageSubTitle]',
        canShowOnMap: false,
      ),
    );
    registerFallbackValue(RouteDetailsModel(0xFFFFFF, '[NoPageTitle]', '[NoPageSubTitle]'));
    registerFallbackValue(
      SettingsModel(
        pageTitle: '[NoPageTitle]',
        routeDbSectionTitle: '[NoSectionTitle]',
        routeDbIdLabel: '[NoRouteDbId]',
        routeDbUpdateLabel: '[NoRouteDbUpdateLabel]',
        routeDbFileSelectionActionLabel: '[NoFileSelectionActionLabel]',
        routeDbFileSelectionFieldLabel: '[NoFileSelectionFieldLabel]',
        routeDbUpdateInProgressLabel: '[NoProgressLabel]',
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
    ///    creation date as label and don't send a status message.
    ///  - If it gets null, deactivate the routeDB domain in the UI, send a special "No DB
    ///    available" label and send a status message.
    ///  - Provided data attributions must be forwarded correctly (if there is a DB at all)
    group('updateRouteDbStatus(): creation date', () {
      /// Make sure the correct values are sent to the UI when the route DB status is changed. If
      /// there is a route DB date, the creation timestamp must be formatted correctly.
      final List<(DateTime?, String)> testParams = <(DateTime?, String)>[
        (DateTime(2023, 1, 2, 3, 4), '02.01.2023 03:04'), // minimal digit value
        (DateTime(2023, 12, 31, 23, 59), '31.12.2023 23:59'), // full digit values
        (DateTime(2024, 4, 16, 13, 9), '16.04.2024 13:09'), // mixed
        (null, 'Keine'), // no timestamp given
      ];

      for (final (DateTime?, String) args in testParams) {
        DateTime? inputDate = args.$1;
        String expectedLabel = args.$2;
        test('db date = $inputDate', () {
          ApplicationWidePresenter presenter = ApplicationWidePresenter();
          presenter.updateRouteDbStatus(inputDate, <DataSourceAttribution>[]);

          final Matcher availabilityMessageMatcher = inputDate != null ? isNull : isNotEmpty;
          verify(
            () => fakeUi.updateRouteDbStatus(
              activated: inputDate != null,
              label: expectedLabel,
              dataSourceAttributions: <ListViewItem>[],
              statusMessage: any(named: 'statusMessage', that: availabilityMessageMatcher),
            ),
          ).called(1);
        });
      }
    });

    group('updateRouteDbStatus(): data attribution', () {
      tearDown(() async {
        // Reset the mocks after each test case
        await di.shutdown();
        di.registerSingleton<ApplicationUiBoundary>(() => fakeUi);
      });

      /// Make sure the correct values are sent to the UI when the route DB status is changed. If
      /// there is a route DB date, the data attribution must be forwarded correctly.
      final DateTime fakeCreationDate = DateTime(2023, 12, 31, 23, 59);
      final List<(List<DataSourceAttribution>, List<ListViewItem>)> testParams =
          <(List<DataSourceAttribution>, List<ListViewItem>)>[
            (
              // All data fields of the attribution object must be handled correctly
              <DataSourceAttribution>[
                DataSourceAttribution(
                  id: 13,
                  label: 'A great source of data',
                  url: 'https://www.example.com',
                  attribution: 'A cool content creator',
                  license: 'EUPL',
                ),
              ],
              <ListViewItem>[
                ListViewItem(
                  'A great source of data',
                  subTitle: 'A cool content creator (EUPL)',
                  content: 'https://www.example.com',
                  itemId: 13,
                ),
              ],
            ),
            (
              // License is missing
              <DataSourceAttribution>[
                DataSourceAttribution(
                  id: 42,
                  label: 'A great source of data',
                  url: 'https://www.example.com',
                  attribution: 'A cool content creator',
                ),
              ],
              <ListViewItem>[
                ListViewItem(
                  'A great source of data',
                  subTitle: 'A cool content creator',
                  content: 'https://www.example.com',
                  itemId: 42,
                ),
              ],
            ),
            (
              // No data at all
              <DataSourceAttribution>[], <ListViewItem>[],
            ),
            (
              // Multiple sources
              <DataSourceAttribution>[
                DataSourceAttribution(
                  id: 1,
                  label: 'Source 1',
                  url: '[url1]',
                  attribution: 'Author 1',
                  license: 'EUPL',
                ),
                DataSourceAttribution(
                  id: 2,
                  label: 'Source 2',
                  url: '[url2]',
                  attribution: 'Author 2',
                ),
              ],
              <ListViewItem>[
                ListViewItem(
                  'Source 1',
                  subTitle: 'Author 1 (EUPL)',
                  content: '[url1]',
                  itemId: 1,
                ),
                ListViewItem(
                  'Source 2',
                  subTitle: 'Author 2',
                  content: '[url2]',
                  itemId: 2,
                ),
              ],
            ),
          ];

      for (final (List<DataSourceAttribution>, List<ListViewItem>) args in testParams) {
        List<DataSourceAttribution> inputAttribution = args.$1;
        List<ListViewItem> expectedListItems = args.$2;
        test('attribution = $inputAttribution', () async {
          FakeUi ui = FakeUi();
          await di.shutdown();
          di.registerSingleton<ApplicationUiBoundary>(() => ui);

          ApplicationWidePresenter presenter = ApplicationWidePresenter();
          presenter.updateRouteDbStatus(fakeCreationDate, inputAttribution);

          expect(ui.dataSourceItems.length, equals(expectedListItems.length));
          for (int i = 0; i < ui.dataSourceItems.length; i++) {
            ListViewItem outputItem = ui.dataSourceItems[i];
            ListViewItem inputItem = expectedListItems[i];
            expect(outputItem.mainTitle, equals(inputItem.mainTitle));
            expect(outputItem.subTitle, equals(inputItem.subTitle));
            expect(outputItem.content, equals(inputItem.content));
            expect(outputItem.itemId, equals(inputItem.itemId));
          }
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
          Summit summit = Summit(42, 'Mount Mock', 'Mock Area', summitPosition);
          presenter.showSummitDetails(summit);

          Matcher summitModelMatcher = isA<SummitDetailsModel>()
              .having((SummitDetailsModel m) => m.pageTitle, 'pageTitle', equals(summit.name))
              .having(
                (SummitDetailsModel m) => m.pageSubTitle,
                'pageSubTitle',
                equals(summit.sector),
              )
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
      Route selectedRoute = Route(
        id: 42,
        routeName: 'Via Exempli',
        grade: Difficulty(af: 5),
        stars: 0,
        dangerous: false,
        routeRating: 2.4,
      );
      presenter.showRouteDetails(selectedRoute);

      Matcher routeModelMatcher = isA<RouteDetailsModel>()
          .having((RouteDetailsModel m) => m.routeDataId, 'dataID', selectedRoute.id)
          .having((RouteDetailsModel m) => m.pageTitle, 'pageTitle', selectedRoute.routeName)
          .having(
            (RouteDetailsModel m) => m.pageSubTitle,
            'pageSubTitle',
            'V',
          );
      verify(() => fakeUi.showRouteDetails(any(that: routeModelMatcher))).called(1);
    });
  });

  /// Ensure the correct grade labels are created for given input data.
  group('SaxonGradeLabelCreator', () {
    SaxonGradeLabelCreator creator = SaxonGradeLabelCreator();

    const Map<int, String> gradeLabels = <int, String>{
      1: 'I',
      2: 'II',
      3: 'III',
      4: 'IV',
      5: 'V',
      6: 'VI',
      7: 'VIIa',
      8: 'VIIb',
      9: 'VIIc',
      10: 'VIIIa',
      11: 'VIIIb',
      12: 'VIIIc',
      13: 'IXa',
      14: 'IXb',
      15: 'IXc',
      16: 'Xa',
      17: 'Xb',
      18: 'Xc',
      19: 'XIa',
      20: 'XIb',
      21: 'XIc',
      22: 'XIIa',
      23: 'XIIb',
      24: 'XIIc',
      25: 'XIIIa',
      26: 'XIIIb',
      27: 'XIIIc',
      28: 'XIVa',
      29: 'XIVb',
      30: 'XIVc',
    };

    // All jump grades
    List<(Difficulty, int, bool, String)> testParams = <(Difficulty, int, bool, String)>[];
    for (int i = 1; i < 8; i++) {
      testParams.add((Difficulty(jump: i), 0, false, '$i'));
    }
    // All climbing grades
    for (int i = 1; i <= gradeLabels.length; i++) {
      testParams.add((Difficulty(af: i), 0, false, gradeLabels[i]!));
    }
    for (int i = 1; i <= gradeLabels.length; i++) {
      final String expectedLabel = gradeLabels[i]!;
      testParams.add((Difficulty(ou: i), 0, false, '($expectedLabel)'));
    }
    for (int i = 1; i <= gradeLabels.length; i++) {
      final String expectedLabel = gradeLabels[i]!;
      testParams.add((Difficulty(ou: i), 0, false, '($expectedLabel)'));
    }
    // Stars and danger marks
    testParams.addAll(<(Difficulty, int, bool, String)>[
      (Difficulty(af: 7), 2, false, '** VIIa'),
      (Difficulty(af: 5), 1, false, '* V'),
      (Difficulty(af: 6), 0, true, '! VI'),
      (Difficulty(af: 13), 1, true, '! * IXa'),
      (Difficulty(af: 8), 2, true, '! ** VIIb'),
    ]);
    // Some Combinations
    testParams.addAll(<(Difficulty, int, bool, String)>[
      (Difficulty(af: 7, ou: 9), 0, false, 'VIIa (VIIc)'),
      (Difficulty(af: 5, rp: 6), 0, false, 'V RP VI'),
      (Difficulty(jump: 2, af: 3), 0, false, '2/III'),
      (Difficulty(af: 10, ou: 11, rp: 9), 0, false, 'VIIIa (VIIIb) RP VIIc'),
      (Difficulty(af: 3, ou: 5, rp: 4), 0, false, 'III (V) RP IV'),
      (Difficulty(jump: 1, af: 4, ou: 5, rp: 3), 0, false, '1/IV (V) RP III'),
      (Difficulty(jump: 3, af: 8, ou: 10, rp: 9), 0, false, '3/VIIb (VIIIa) RP VIIc'),
      (Difficulty(af: 5, ou: 7, rp: 4), 1, true, '! * V (VIIa) RP IV'),
    ]);

    for (final (Difficulty, int, bool, String) params in testParams) {
      Difficulty grade = params.$1;
      int stars = params.$2;
      bool danger = params.$3;
      String expectedLabel = params.$4;
      test('Combination: $grade', () {
        Route route = Route(
          id: 42,
          routeName: 'Example Route',
          grade: grade,
          stars: stars,
          dangerous: danger,
        );
        expect(creator.createGradeLabel(route), expectedLabel);
      });
    }
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
