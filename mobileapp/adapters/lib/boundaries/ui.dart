///
/// Definition of the boundary between UI adapters (`adapters` ring) and a concrete UI
/// implementation (`infrastructure` ring).
///
library;

/// Model that provides all data needed to display the app's main menu to the UI.
class MainMenuModel {
  /// Header string for the main menu
  final String menuHeader;

  /// List item for the journal domain.
  final ListViewItem journalItem;

  /// List item for the route db domain.
  final ListViewItem routedbItem;

  /// List item for the knowledge base domain.
  final ListViewItem knowledgebaseItem;

  /// List item for the settings domain.
  final ListViewItem settingsItem;

  /// Constructor for directly initializing all members.
  const MainMenuModel(
    this.menuHeader,
    this.journalItem,
    this.routedbItem,
    this.knowledgebaseItem,
    this.settingsItem,
  );
}

/// Abstract representation of a graphical symbol.
///
/// This enum defines what should be symbolized by icon, which doesn't necessarily mean it has to
/// be a single icon only at all. The concrete presentation is up to the UI implementation (which
/// may also decide for multiple icons or a pure text display, of course).
enum Glyph {
  /// Represents a "checked" or "activated" state.
  checked,

  /// Represents the logo for the journal application domain.
  logoJournal,

  /// Represents the logo for the knowledge base application domain.
  logoKnowledgeBase,

  /// Represents the logo for the route database application domain.
  logoRouteDb,

  /// Represents the logo for the application settings.
  logoSettings,

  /// Represents the lowest possible score in some rating (e.g. "zero points").
  scoreLowest,

  /// Represents a lower-middle score in some rating.
  scoreLowerMid,

  /// Represents an upper-middle score in some rating.
  scoreUpperMid,

  /// Represents the highest possible score in some rating (e.g. "all points").
  scoreHighest,
}

/// Represents the color a certain glyph shall be drawn with.
///
/// This is a hint which influences the drawing color to choose. The concrete color representation
/// (e.g. RGB value) is up to the UI, though, and may be ignored under certain conditions (e.g.
/// monochrome display or inverted/high contrast display settings). If [unspecified], the UI can
/// decide freely.
enum ColorHint {
  /// No special color hint shall be given (usually the default).
  unspecified,

  /// A green/greenish color representing something positive.
  greenPositive,

  /// A red/reddish colour represent something negative.
  redNegative,

  /// An explicit neutral color.
  neutral,
}

/// Abstract representation of a graphical symbol.
///
/// This class defines what should be symbolized by icon, which doesn't necessarily mean it has to
/// a single icon only. The concrete presentation is up to the UI implementation (which may also
/// decide for a pure text display, of course).
class IconDefinition {
  /// The symbol which should be presented.
  final Glyph glyph;

  /// The color hint for drawing the displayed symbol.
  final ColorHint colorHint;

  /// Constructor for directly initializing all members.
  const IconDefinition(this.glyph, [this.colorHint = ColorHint.unspecified]);
}

/// Model that provides all data needed to display a single knowledge base document to the UI.
class KnowledgebaseModel {
  /// Title of the document being displayed.
  final String documentTitle;

  /// Markdown content of the document being displayed.
  final String documentContent;

  /// Constructor for directly initializing all members.
  KnowledgebaseModel(this.documentTitle, this.documentContent);
}

/// Model that provides all static data needed to display the empty summit list page to the UI.
///
/// "Static" means, that this data does not change while the page is shown, so it can be provided
/// once during the initial page display.
class SummitListModel {
  /// Title of the summit list page.
  final String pageTitle;

  /// Help message/Hint to be displayed in the search bar.
  final String searchBarHint;

  /// Constructor for directly initializing all members.
  SummitListModel(this.pageTitle, this.searchBarHint);
}

/// Internal ID to uniquely identify a single data item.
///
/// A value of this type can be used to e.g. identify the selected item in a list. It is not meant
/// to be shown to the user.
typedef ItemDataId = int;

/// Describes the contents of a single list item to be displayed by the UI in a generic way.
///
/// The exact appearance is defined by the concrete UI implementation. Also, the data that is
/// displayed at all may depend on the context.
class ListViewItem {
  /// The main label of the item, displayed most prominently. This is the only property that must
  /// always be available and is always displayed.
  final String mainTitle;

  /// An optional sub label which is displayed less prominently (e.g. below) the main one.
  final String? subTitle;

  /// A graphical icon to display at the beginning (e.g. before the mainTitle text) of the list
  /// item.
  final IconDefinition? icon;

  /// A graphical icon to display at the end (e.g. after the mainTitle text) of the list item.
  final IconDefinition? endIcon;

  /// Optional item content.
  ///
  /// Expect this to be a long, multi-line string.
  String? content;

  /// Unique identifier of this item. If a list item is clicked, this ID is passed to the handler
  /// to identify the clicked item. Without an ID, the item cannot be clicked at all.
  ItemDataId? itemId;

  /// Constructor for directly initializing all members.
  ListViewItem(this.mainTitle, {this.subTitle, this.icon, this.endIcon, this.content, this.itemId});
}

/// Model that provides all static data needed to display the summit details page to the UI.
///
/// "Static" means, that this data does not change while the page is shown, so it can be provided
/// once during the initial page display.
class SummitDetailsModel {
  /// Internal ID of the summit whose details shall be displayed.
  ItemDataId summitDataId;

  /// Title of the summit details page.
  final String pageTitle;

  /// Flag for displaying if the summit can be shown on a map (true) or not (false, e.g. because it
  /// lacks a geo position).
  final bool canShowOnMap;

  /// Constructor for directly initializing all members.
  SummitDetailsModel(this.summitDataId, this.pageTitle, this.canShowOnMap);
}

/// Model that provides all static data needed to display the route details page to the UI.
///
/// "Static" means, that this data does not change while the page is shown, so it can be provided
/// once during the initial page display.
class RouteDetailsModel {
  /// Internal ID of the route whose details shall be displayed.
  ItemDataId routeDataId;

  /// Title of the route details page.
  final String pageTitle;

  /// Sub title of the route details page.
  final String pageSubTitle;

  /// Constructor for directly initializing all members.
  RouteDetailsModel(this.routeDataId, this.pageTitle, this.pageSubTitle);
}

/// Model that provides all static data needed to display the settings page to the UI.
///
/// "Static" means, that this data does not change while the page is shown, so it can be provided
/// once during the initial page display. Certain UI implementations may choose to ignore some of
/// those fields on certain platforms.
class SettingsModel {
  /// Title of the settings page.
  final String pageTitle;

  /// Label to use for the route database identifier.
  final String routeDbIdLabel;

  /// Label to use for the "select new route database to import" action.
  final String routeDbFileSelectionActionLabel;

  /// Label to use for the actual route db file selection widget.
  final String routeDbFileSelectionFieldLabel;

  /// Constructor for directly initializing all members.
  SettingsModel({
    required this.pageTitle,
    required this.routeDbIdLabel,
    required this.routeDbFileSelectionActionLabel,
    required this.routeDbFileSelectionFieldLabel,
  });
}

/// Boundary interface to the concrete, domain-independent part of the UI implementation.
///
/// This interface provides general, application-wide UI operations. Domain specific concerns are
/// separated into more specialized sub-interfaces.
abstract interface class ApplicationUiBoundary {
  /// Initializes the user interface for the application with the display name [appName].
  ///
  /// The provided [appName] can be displayed e.g. in some title or header bar, the [splashString]
  /// is displayed during the startup phase before the UI is ready to for user interactions. The
  /// [menuModel] are used e.g. for the main navigation menu.
  void initializeUserInterface(String appName, String splashString, MainMenuModel menuModel);

  /// Notify the UI about changed route database status.
  ///
  /// This will update the display with the given status information:
  /// - [routeDbActivated]: The activation status of the route database (true: enabled, false:
  ///   disabled)
  /// - [routeDbIdentifier]: A label for identifying the current route database (may of course be
  ///   something like 'None' if the route database is disabled)
  /// - [availabilityMessage]: A message with more detailed information about the route database
  ///   status. Set to `null` to not display any additional hint at all.
  void updateRouteDbStatus({
    required bool routeDbActivated,
    required String routeDbIdentifier,
    String? availabilityMessage,
  });

  /// Request the UI to display the *Summit List* screen based on the provided [model].
  ///
  /// The list data must be sent separately by calling [updateSummitList] afterwards.
  void showSummitList(SummitListModel model);

  /// Notify the UI about a new summit list.
  ///
  /// This will update the display with the new [summitItems] as necessary.
  void updateSummitList(List<ListViewItem> summitItems);

  /// Request the UI to display the *Summit Details* screen based on the provided [model].
  ///
  /// The list of routes onto this summit must be sent separately by calling [updateRouteList]
  /// afterwards.
  void showSummitDetails(SummitDetailsModel model);

  /// Notify the UI about a new route list.
  ///
  /// This will update the display with the new [routeItems] and the new [sortMenuItems] (sort menu)
  /// as necessary.
  void updateRouteList(List<ListViewItem> routeItems, List<ListViewItem> sortMenuItems);

  /// Request the UI to display the *Route Details* screen based on the provided [model].
  ///
  /// The list of posts found for this route must be sent separately by calling [updatePostList]
  /// afterwards.
  void showRouteDetails(RouteDetailsModel model);

  /// Notify the UI about a new post list.
  ///
  /// This will update the display with the new [postItems] and the new [sortMenuItems] (sort menu)
  /// as necessary.
  void updatePostList(List<ListViewItem> postItems, List<ListViewItem> sortMenuItems);

  /// Request the UI to display the *Journal* screen.
  void switchToJournal();

  /// Request the UI to display the provided [document] on the  *Knowledge Base* screen.
  void showKnowledgebase(KnowledgebaseModel document);

  /// Request the UI to display the *Settings* screen based on the provided [model].
  void showSettings(SettingsModel model);
}
