///
/// Provides the summit details page widget of the *Route DB* domain.
///
library;

import 'dart:async';

import 'package:adapters/boundaries/ui.dart';
import 'package:adapters/controllers.dart';
import 'package:flutter/material.dart';
import 'package:loading_indicator/loading_indicator.dart';
import 'package:provider/provider.dart';

import '../icons.dart';
import '../state.dart';

/// Widget representing the *Summit Details* page.
class SummitDetailsView extends StatefulWidget {
  /// The app drawer (navigation menu) to use.
  final Widget appDrawer;

  /// Notifier providing the current route list state to be displayed.
  final RouteListNotifier routeListState;

  /// Constructor for directly initializing all members.
  const SummitDetailsView(this.appDrawer, this.routeListState, {super.key});

  @override
  State<StatefulWidget> createState() {
    return _SummitDetailsViewState();
  }
}

class _SummitDetailsViewState extends State<SummitDetailsView> with SingleTickerProviderStateMixin {
  late TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(vsync: this, length: _TabFactory.getTabCount());
  }

  @override
  Widget build(BuildContext context) {
    final SummitDetailsModel model =
        ModalRoute.of(context)!.settings.arguments! as SummitDetailsModel;

    _TabFactory tabFactory = _TabFactory(widget, model);

    return Scaffold(
      appBar: _buildAppBar(model, tabFactory.getTabs(), tabFactory.getContextMenus(), context),
      body: TabBarView(
        controller: _tabController,
        children: tabFactory.getContentWidgets(),
      ),
      drawer: widget.appDrawer,
      drawerEnableOpenDragGesture: false,
    );
  }

  AppBar _buildAppBar(
    SummitDetailsModel model,
    List<Tab> tabs,
    List<Widget> contextMenus,
    BuildContext context,
  ) {
    return AppBar(
      title: Column(
        children: <Widget>[
          Text(model.pageTitle),
          Text(model.pageSubTitle, style: Theme.of(context).textTheme.bodyMedium),
        ],
      ),
      centerTitle: true,
      backgroundColor: Colors.lightGreen,
      actions: <Widget>[
        IconButton(
          onPressed: model.canShowOnMap
              ? () {
                  _onShowOnMap(model.summitDataId);
                }
              : null,
          icon: const Icon(Icons.map),
        ),
        IconButton(
          onPressed: () {
            _showContextMenu(contextMenus[_tabController.index], context);
          },
          icon: const Icon(Icons.menu_open),
        ),
      ],
      bottom: TabBar(
        controller: _tabController,
        tabs: tabs,
      ),
    );
  }

  void _showContextMenu(Widget contextMenu, BuildContext context) {
    unawaited(
      showModalBottomSheet(
        context: context,
        builder: (BuildContext context) => contextMenu,
      ),
    );
  }

  void _onShowOnMap(ItemDataId summitDataId) {
    RouteDbController controller = RouteDbController();
    controller.requestShowSummitOnMap(summitDataId);
  }
}

/// Context menu to be shown when the "routes" tab is active.
class SummitRoutesContextMenu extends StatelessWidget {
  final SummitDetailsModel _model;
  final RouteListNotifier _state;

  /// Factory for creating icon widgets.
  static const IconWidgetFactory _iconFactory = IconWidgetFactory();

  /// Constructor for directly initializing all members.
  const SummitRoutesContextMenu(this._model, this._state, {super.key});

  @override
  Widget build(BuildContext context) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: _createContextMenuitems(context),
    );
  }

  List<Widget> _createContextMenuitems(BuildContext context) {
    List<ListTile> menuItems = <ListTile>[];
    for (final ListViewItem item in _state.getSortMenuItems()) {
      menuItems.add(
        ListTile(
          title: Text(item.mainTitle),
          trailing: _iconFactory.getIconWidget(item.endIcon),
          onTap: () {
            _onOrderingChanged(_model.summitDataId, item.itemId!);
            Navigator.pop(context);
          },
        ),
      );
    }
    return menuItems;
  }

  void _onOrderingChanged(ItemDataId summitDataId, ItemDataId sortMenuItemId) {
    RouteDbController controller = RouteDbController();
    controller.requestRouteListSorting(summitDataId, sortMenuItemId);
  }
}

/// A factory that creates all the tabs and associated widgets.
///
/// Most methods return a list of objects, their indices are synchronized, meaning: Index 1 of the
/// [getTabs()] return value correspond to index 1 of the [getContentWidgets()] return value and so
/// on.
///
/// This factory doesn't actually build or define tab contents, but is responsible to decide which
/// concrete classes are used and in which order.
class _TabFactory {
  final SummitDetailsView _pageWidget;
  final SummitDetailsModel _pageModel;

  _TabFactory(this._pageWidget, this._pageModel);

  /// Return the number of available tabs.
  static int getTabCount() {
    return 1;
  }

  /// Return all the tab widgets (i.e. the icons to click on for selecting one) to use.
  List<Tab> getTabs() {
    return const <Tab>[
      Tab(
        icon: Icon(Icons.hiking), // Better: Icons.elevation, but not available yet
      ),
    ];
  }

  /// Return all the content widgets that should be shown.
  List<Widget> getContentWidgets() {
    return <Widget>[
      SummitRoutesView(_pageWidget.routeListState),
    ];
  }

  /// Return all the context menu widgets that are associated with the single tabs.
  List<Widget> getContextMenus() {
    return <Widget>[
      SummitRoutesContextMenu(_pageModel, _pageWidget.routeListState),
    ];
  }
}

/// The widget being shown when the "routes" tab is active.
class SummitRoutesView extends StatelessWidget {
  final RouteListNotifier _state;

  /// Factory for creating icon widgets.
  static const IconWidgetFactory _iconFactory = IconWidgetFactory();

  /// Constructor for directly initializing all members.
  const SummitRoutesView(this._state, {super.key});

  @override
  Widget build(BuildContext context) {
    return ChangeNotifierProvider<RouteListNotifier>.value(
      value: _state,
      child: Consumer<RouteListNotifier>(
        builder: (BuildContext context, RouteListNotifier state, Widget? child) {
          if (state.routesLoaded()) {
            return ListView.builder(
              itemCount: _state.getRouteCount(),
              itemBuilder: (BuildContext context, int index) {
                final ListViewItem route = _state.getRouteItem(index);
                return ListTile(
                  title: Text(route.mainTitle),
                  subtitle: Text(route.subTitle ?? ''),
                  trailing: _iconFactory.getIconWidget(route.endIcon),
                  onTap: () {
                    _onRouteTap(route.itemId!);
                  },
                );
              },
            );
          } else {
            return _showLoadingIndicator();
          }
        },
      ),
    );
  }

  Widget _showLoadingIndicator() {
    return const LoadingIndicator(
      indicatorType: Indicator.ballClipRotateMultiple,
      colors: <Color>[Colors.lightGreen],
    );
  }

  void _onRouteTap(ItemDataId routeDataId) {
    RouteDbController controller = RouteDbController();
    controller.requestRouteDetails(routeDataId);
  }
}
