///
/// Provides the summit list page widget of the *Route DB* domain.
///
library;

import 'package:adapters/boundaries/ui.dart';
import 'package:adapters/controllers.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../state.dart';

/// Widget representing the *Summit List* page.
class SummitListView extends StatelessWidget {
  /// The app drawer (navigation menu) to use.
  final Widget _appDrawer;

  /// Notifier providing the current summit list state to be displayed.
  final SummitListNotifier _summitListState;

  final TextEditingController _controller = TextEditingController();

  /// Constructor for directly initializing all members.
  SummitListView(this._appDrawer, this._summitListState, {super.key});

  @override
  Widget build(BuildContext context) {
    final SummitListModel model = ModalRoute.of(context)!.settings.arguments! as SummitListModel;
    return Scaffold(
      appBar: _appBar(model),
      body: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: <Widget>[_searchBar(model.searchBarHint), _listView()],
      ),
      drawer: _appDrawer,
    );
  }

  AppBar _appBar(SummitListModel model) {
    return AppBar(
      title: Text(model.pageTitle),
      centerTitle: true,
      backgroundColor: Colors.lightGreen,
    );
  }

  void _filterSummits(String query) {
    RouteDbController controller = RouteDbController();
    controller.requestFilterSummitList(query);
  }

  Widget _listView() {
    return ChangeNotifierProvider<SummitListNotifier>.value(
      value: _summitListState,
      child: Consumer<SummitListNotifier>(
        builder: (BuildContext context, SummitListNotifier state, Widget? child) {
          return Expanded(
            child: ListView.builder(
              itemCount: state.getSummitCount(),
              itemBuilder: (BuildContext context, int index) {
                final ListViewItem summit = state.getSummitItem(index);
                return ListTile(
                  title: Text(summit.mainTitle),
                  onTap: () {
                    _onSummitTap(summit.itemId!);
                  },
                );
              },
            ),
          );
        },
      ),
    );
  }

  Container _searchBar(String searchBarHint) {
    return Container(
      margin: const EdgeInsets.only(top: 10, left: 10, right: 10),
      decoration: BoxDecoration(
        boxShadow: <BoxShadow>[
          BoxShadow(color: Colors.black.withValues(alpha: 0.11), blurRadius: 40, spreadRadius: 0),
        ],
      ),
      child: TextField(
        controller: _controller,
        onChanged: _filterSummits,
        decoration: InputDecoration(
          filled: true,
          fillColor: Colors.white,
          contentPadding: const EdgeInsets.all(15),
          hintText: searchBarHint,
          prefixIcon: const Padding(padding: EdgeInsets.all(12), child: Icon(Icons.search)),
          suffixIcon: IconButton(
            icon: const Icon(Icons.clear),
            onPressed: () {
              _controller.clear();
              _filterSummits('');
            },
          ),
          border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(15),
            borderSide: BorderSide.none,
          ),
        ),
      ),
    );
  }

  void _onSummitTap(ItemDataId summitDataId) {
    RouteDbController controller = RouteDbController();
    controller.requestSummitDetails(summitDataId);
  }
}
