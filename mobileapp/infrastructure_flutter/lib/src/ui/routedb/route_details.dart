///
/// Provides the route details page widget of the *Route DB* domain.
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
import '../widgets/carousel.dart';
import '../widgets/centered_text.dart';

/// Widget representing a single post with the post list.
class _PostItem extends StatelessWidget {
  /// The post data to be displayed.
  final ListViewItem post;

  /// Factory for creating icon widgets.
  static const IconWidgetFactory _iconFactory = IconWidgetFactory();

  const _PostItem({required this.post});

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.all(10),
      child: Padding(
        padding: const EdgeInsets.all(10),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: <Widget>[
                Text(post.mainTitle, style: const TextStyle(fontWeight: FontWeight.bold)),
                _iconFactory.getIconWidget(post.endIcon),
              ],
            ),
            const SizedBox(height: 5),
            Text(post.subTitle!),
            const SizedBox(height: 5),
            Text(post.content!),
            const SizedBox(height: 5),
            Text(
              post.bottomLine!,
              style: const TextStyle(fontSize: 10, fontWeight: FontWeight.w300),
            ),
          ],
        ),
      ),
    );
  }
}

/// Widget representing a single item in the directions carousel.
class _DirectionsItem extends StatelessWidget {
  /// The data item to display.
  final ListViewItem _dataItem;

  /// Constructor for directly initializing all members.
  const _DirectionsItem(this._dataItem);

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: <Widget>[
        Text(
          _dataItem.mainTitle,
        ),
        const SizedBox(height: 5),
        Text(
          _dataItem.bottomLine!,
          style: const TextStyle(
            fontSize: 10,
            fontWeight: FontWeight.w300,
          ),
        ),
      ],
    );
  }
}

/// Widget for displaying "global" properties of the route itself, not of all the single posts.
class _RoutePropertiesView extends StatelessWidget {
  /// The model to retrieve route data from.
  final RouteDetailsModel model;

  /// Constructor for directly initializing all members.
  const _RoutePropertiesView(this.model);

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(top: 10, left: 10, right: 10),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          WidgetCarousel(
            <Widget>[
              for (final ListViewItem item in model.directionsItems) _DirectionsItem(item),
            ],
          ),
          const Divider(),
        ],
      ),
    );
  }
}

/// Widget representing the *Route Details* page.
// TODO(aardjon): Refactor this to the generic approach of using DeferableOptionalDataListView.
class RouteDetailsView extends StatelessWidget {
  /// The app drawer (navigation menu) to use.
  final Widget _appDrawer;

  /// Notifier providing the current post list state to be displayed.
  final PostListNotifier _postListState;

  /// Factory for creating icon widgets.
  static const IconWidgetFactory _iconFactory = IconWidgetFactory();

  /// Constructor for directly initializing all members.
  const RouteDetailsView(this._appDrawer, this._postListState, {super.key});

  @override
  Widget build(BuildContext context) {
    final RouteDetailsModel model =
        ModalRoute.of(context)!.settings.arguments! as RouteDetailsModel;

    return ChangeNotifierProvider<PostListNotifier>.value(
      value: _postListState,
      child: Consumer<PostListNotifier>(
        builder: (BuildContext context, PostListNotifier state, Widget? child) {
          if (state.postsLoaded()) {
            return Scaffold(
              appBar: _appBar(model, state, context),
              body: _buildDataView(model, state, context),
              drawer: _appDrawer,
              drawerEnableOpenDragGesture: false,
            );
          } else {
            return _showLoadingIndicator();
          }
        },
      ),
    );
  }

  AppBar _appBar(RouteDetailsModel model, PostListNotifier state, BuildContext context) {
    return AppBar(
      title: Column(
        children: <Widget>[
          Text(model.pageTitle, style: const TextStyle(fontSize: 20)),
          Text(model.pageSubTitle, style: const TextStyle(fontSize: 14)),
        ],
      ),
      centerTitle: true,
      backgroundColor: Colors.lightGreen,
      actions: <Widget>[
        IconButton(
          onPressed: model.canShowEntryOnMap
              ? () {
                  _onShowOnMap(model.routeDataId);
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
          icon: const Icon(Icons.menu_open),
        ),
      ],
    );
  }

  Widget _createFilterMenu(RouteDetailsModel model, PostListNotifier state, BuildContext context) {
    List<ListTile> menuItems = <ListTile>[];
    for (final ListViewItem item in state.getSortMenuItems()) {
      menuItems.add(
        ListTile(
          title: Text(item.mainTitle),
          trailing: _iconFactory.getIconWidget(item.endIcon),
          onTap: () {
            _onOrderingChanged(model.routeDataId, item.itemId!);
            Navigator.pop(context);
          },
        ),
      );
    }
    return Column(mainAxisSize: MainAxisSize.min, children: menuItems);
  }

  Widget _buildDataView(RouteDetailsModel model, PostListNotifier state, BuildContext context) {
    if (model.directionsItems.isEmpty && state.getPostCount() == 0) {
      return CenteredText(model.noDataMessage);
    }
    return _listView(model, state, context);
  }

  Widget _listView(RouteDetailsModel model, PostListNotifier state, BuildContext context) {
    final int listItemIndexOffset = model.directionsItems.isNotEmpty ? 1 : 0;
    return ListView.builder(
      itemCount: state.getPostCount() + listItemIndexOffset,
      itemBuilder: (BuildContext context, int index) {
        if (model.directionsItems.isNotEmpty && index == 0) {
          return _RoutePropertiesView(model);
        }
        final ListViewItem post = state.getPostItem(index - listItemIndexOffset);
        return _PostItem(post: post);
      },
    );
  }

  void _onOrderingChanged(ItemDataId routeDataId, ItemDataId sortMenuItemId) {
    RouteDbController controller = RouteDbController();
    controller.requestPostListSorting(routeDataId, sortMenuItemId);
  }

  void _onShowOnMap(ItemDataId routeDataId) {
    RouteDbController controller = RouteDbController();
    controller.requestShowRouteOnMap(routeDataId);
  }

  Widget _showLoadingIndicator() {
    return const LoadingIndicator(
      indicatorType: Indicator.ballClipRotateMultiple,
      colors: <Color>[Colors.lightGreen],
    );
  }
}
