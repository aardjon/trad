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
class SummitDetailsView extends StatelessWidget {
  /// The app drawer (navigation menu) to use.
  final Widget _appDrawer;

  /// Notifier providing the current route list state to be displayed.
  final RouteListNotifier _routeListState;

  /// Factory for creating icon widgets.
  static const IconWidgetFactory _iconFactory = IconWidgetFactory();

  /// Constructor for directly initializing all members.
  const SummitDetailsView(this._appDrawer, this._routeListState, {super.key});

  @override
  Widget build(BuildContext context) {
    final SummitDetailsModel model =
        ModalRoute.of(context)!.settings.arguments! as SummitDetailsModel;
    return ChangeNotifierProvider<RouteListNotifier>.value(
      value: _routeListState,
      child: Consumer<RouteListNotifier>(
        builder: (BuildContext context, RouteListNotifier state, Widget? child) {
          if (state.routesLoaded()) {
            return Scaffold(
              appBar: _appBar(model, state, context),
              body: _listView(state, context),
              drawer: _appDrawer,
            );
          } else {
            return _showLoadingIndicator();
          }
        },
      ),
    );
  }

  AppBar _appBar(SummitDetailsModel model, RouteListNotifier state, BuildContext context) {
    return AppBar(
      title: Text(model.pageTitle),
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
            unawaited(
              showModalBottomSheet(
                context: context,
                builder: (BuildContext context) => _createFilterMenu(model, state, context),
              ),
            );
          },
          icon: const Icon(Icons.filter_list),
        ),
      ],
    );
  }

  Widget _createFilterMenu(
    SummitDetailsModel model,
    RouteListNotifier state,
    BuildContext context,
  ) {
    List<ListTile> menuItems = <ListTile>[];
    for (final ListViewItem item in state.getSortMenuItems()) {
      menuItems.add(
        ListTile(
          title: Text(item.mainTitle),
          trailing: _iconFactory.getIconWidget(item.endIcon),
          onTap: () {
            _onOrderingChanged(model.summitDataId, item.itemId!);
            Navigator.pop(context);
          },
        ),
      );
    }
    return Column(mainAxisSize: MainAxisSize.min, children: menuItems);
  }

  Widget _listView(RouteListNotifier state, BuildContext context) {
    return ListView.builder(
      itemCount: state.getRouteCount(),
      itemBuilder: (BuildContext context, int index) {
        final ListViewItem route = state.getRouteItem(index);
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
  }

  void _onOrderingChanged(ItemDataId summitDataId, ItemDataId sortMenuItemId) {
    RouteDbController controller = RouteDbController();
    controller.requestRouteListSorting(summitDataId, sortMenuItemId);
  }

  void _onRouteTap(ItemDataId routeDataId) {
    RouteDbController controller = RouteDbController();
    controller.requestRouteDetails(routeDataId);
  }

  void _onShowOnMap(ItemDataId summitDataId) {
    RouteDbController controller = RouteDbController();
    controller.requestShowSummitOnMap(summitDataId);
  }

  Widget _showLoadingIndicator() {
    return const LoadingIndicator(
      indicatorType: Indicator.ballClipRotateMultiple,
      colors: <Color>[Colors.lightGreen],
    );
  }
}
