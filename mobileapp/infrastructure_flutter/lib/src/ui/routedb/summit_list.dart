///
/// Provides the summit list page widget of the *Route DB* domain.
///
library;

import 'package:adapters/boundaries/ui.dart';
import 'package:adapters/controllers.dart';
import 'package:flutter/material.dart';

import '../state.dart';
import '../widgets/listviews.dart';

/// Widget representing the *Summit List* page.
class SummitListPage extends StatelessWidget {
  /// The app drawer (navigation menu) to use.
  final Widget _appDrawer;

  /// Notifier providing the current summit list state to be displayed.
  final DeferableOptionalDataListNotifier _summitListState;

  /// Constructor for directly initializing all members.
  const SummitListPage(this._appDrawer, this._summitListState, {super.key});

  @override
  Widget build(BuildContext context) {
    final SummitListModel model = ModalRoute.of(context)!.settings.arguments! as SummitListModel;
    return Scaffold(
      appBar: _appBar(model),
      body: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: <Widget>[_filterWidget(model, context), _listView()],
      ),
      drawer: _appDrawer,
      drawerEnableOpenDragGesture: false,
    );
  }

  AppBar _appBar(SummitListModel model) {
    return AppBar(
      title: Text(model.pageTitle),
      centerTitle: true,
      backgroundColor: Colors.lightGreen,
    );
  }

  Widget _filterWidget(SummitListModel model, BuildContext context) {
    return SummitFilterBar(
      nameFilterHint: model.searchBarHint,
      sectorFilterItems: model.searchBarSectors,
      initialSelectedIndex: model.searchBarInitialSectorIndex,
      onFilterChanged: _filterSummits,
    );
  }

  Widget _listView() {
    return Expanded(child: SummitListView(_summitListState));
  }

  void _filterSummits(String nameFilter, int? areaFilter) {
    RouteDbController controller = RouteDbController();
    controller.requestFilterSummitList(nameFilter, areaFilter);
  }
}

/// Widget for defining a summit filter condition.
///
/// This widget lets the user select a sector and/or enter (part of) a summit name. The application
/// can then filter the list accordingly. The given function [onFilterChanged] is called whenever
/// the filter ist changed by the user.
class SummitFilterBar extends StatefulWidget {
  /// A label for describing the name filter text box to the user.
  final String nameFilterHint;

  /// The sector items to be available for selection.
  final List<ListViewItem> sectorFilterItems;

  /// The index of the [sectorFilterItems] item to be selected initially.
  final int initialSelectedIndex;

  /// Function to call after the user changed the filter condition.
  /// Note that it is not called when the user set the same conition again.
  final void Function(String nameFilter, ItemDataId? sectorFilter) onFilterChanged;

  /// Constructor for directly initializing all members.
  const SummitFilterBar({
    required this.nameFilterHint,
    required this.sectorFilterItems,
    required this.initialSelectedIndex,
    required this.onFilterChanged,
    super.key,
  });

  @override
  State<StatefulWidget> createState() {
    return _SummitFilterBarState();
  }
}

/// State of the [SummitFilterBar] widget.
///
/// The widget state is basically the currently defined filter condition.
class _SummitFilterBarState extends State<SummitFilterBar> {
  final TextEditingController _controller = TextEditingController();

  // The currently entered name string.
  String _nameFilter = '';

  /// ID of the currently selected sector.
  ItemDataId? _selectedArea;

  @override
  void initState() {
    super.initState();
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(top: 10, left: 10, right: 10),
      decoration: BoxDecoration(
        boxShadow: <BoxShadow>[
          BoxShadow(color: Colors.black.withValues(alpha: 0.11), blurRadius: 40, spreadRadius: 0),
        ],
      ),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        spacing: 5,
        children: <Widget>[_sectorSelectionWidget(context), _nameSearchWidget()],
      ),
    );
  }

  Widget _nameSearchWidget() {
    return TextField(
      controller: _controller,
      onChanged: (String filterText) {
        setState(() {
          _nameFilter = filterText;
          widget.onFilterChanged(_nameFilter, _selectedArea);
        });
      },
      decoration: InputDecoration(
        filled: true,
        fillColor: Colors.white,
        contentPadding: const EdgeInsets.all(15),
        hintText: widget.nameFilterHint,
        prefixIcon: const Padding(padding: EdgeInsets.all(12), child: Icon(Icons.search)),
        suffixIcon: IconButton(
          icon: const Icon(Icons.clear),
          onPressed: () {
            _controller.clear();
            setState(() {
              _nameFilter = '';
              _selectedArea = null;
              widget.onFilterChanged(_nameFilter, _selectedArea);
            });
          },
        ),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(15),
          borderSide: BorderSide.none,
        ),
      ),
    );
  }

  Widget _sectorSelectionWidget(BuildContext context) {
    final List<DropdownMenuEntry<int?>> entries = List<DropdownMenuEntry<int?>>.from(
      widget.sectorFilterItems.map<DropdownMenuEntry<int?>>(
        (ListViewItem item) => DropdownMenuEntry<int?>(
          label: item.mainTitle,
          value: item.itemId,
        ),
      ),
    );

    return DropdownMenu<ItemDataId?>(
      leadingIcon: const Padding(
        padding: EdgeInsets.all(12),
        child: Icon(Icons.filter_alt_outlined),
      ),
      initialSelection: entries[widget.initialSelectedIndex].value,
      requestFocusOnTap: false,
      expandedInsets: EdgeInsets.zero,
      onSelected: (ItemDataId? areaId) {
        setState(() {
          _selectedArea = areaId;
          widget.onFilterChanged(_nameFilter, _selectedArea);
        });
      },
      dropdownMenuEntries: entries,
    );
  }
}
