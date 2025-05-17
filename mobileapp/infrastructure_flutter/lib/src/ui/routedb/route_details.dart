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
          ],
        ),
      ),
    );
  }
}

/// Widget representing the *Route Details* page.
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

  Widget _listView(PostListNotifier state, BuildContext context) {
    return ListView.builder(
      itemCount: state.getPostCount(),
      itemBuilder: (BuildContext context, int index) {
        final ListViewItem post = state.getPostItem(index);
        return _PostItem(post: post);
      },
    );
  }

  void _onOrderingChanged(ItemDataId routeDataId, ItemDataId sortMenuItemId) {
    RouteDbController controller = RouteDbController();
    controller.requestPostListSorting(routeDataId, sortMenuItemId);
  }

  Widget _showLoadingIndicator() {
    return const LoadingIndicator(
      indicatorType: Indicator.ballClipRotateMultiple,
      colors: <Color>[Colors.lightGreen],
    );
  }
}
