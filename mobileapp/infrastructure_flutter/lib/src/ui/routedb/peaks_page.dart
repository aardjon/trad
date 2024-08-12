import 'package:flutter/material.dart';
import 'package:teufelsturm_viewer/models/peak_data.dart';
import 'package:teufelsturm_viewer/pages/routes_page.dart';
import 'package:teufelsturm_viewer/utils/sqlite_manager.dart';

class PeaksPage extends StatefulWidget {
  const PeaksPage({super.key});

  @override
  State<PeaksPage> createState() => _PeaksPageState();
}

class _PeaksPageState extends State<PeaksPage> {
  late TextEditingController _controller;
  List<PeakData> _allPeaks = <PeakData>[];
  List<PeakData> _filteredPeaks = <PeakData>[];
  final SqliteManager _sqliteManager = SqliteManager();

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: _appBar(),
      body: Column(
        children: <Widget>[
          _searchBar(),
          _listView(),
        ],
      ),
    );
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  void initState() {
    super.initState();
    _controller = TextEditingController();
    _loadPeaksFromDatabase();
  }

  AppBar _appBar() {
    return AppBar(
      title: const Text('Gipfel'),
      centerTitle: true,
      backgroundColor: Colors.lightGreen,
    );
  }

  void _filterPeaks(String query) {
    setState(() {
      _filteredPeaks = _allPeaks
          .where(
            (PeakData? peak) => peak.peakName.toLowerCase().contains(query.toLowerCase()),
          )
          .toList();
    });
  }

  Expanded _listView() {
    return Expanded(
      child: ListView.builder(
        itemCount: _filteredPeaks.length,
        itemBuilder: (BuildContext context, int index) {
          return ListTile(
            title: Text(_filteredPeaks[index].peakName),
            onTap: () {
              Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (BuildContext context) => RoutesPage(
                    peak: _filteredPeaks[index],
                    sqliteManager: _sqliteManager,
                  ),
                ),
              );
            },
          );
        },
      ),
    );
  }

  void _loadPeaksFromDatabase() async {
    List<PeakData> peaks = await _sqliteManager.getAllPeaks();
    setState(() {
      _allPeaks = peaks;
      _filteredPeaks.addAll(_allPeaks);
    });
  }

  Container _searchBar() {
    return Container(
      margin: const EdgeInsets.only(top: 10, left: 10, right: 10),
      decoration: BoxDecoration(
        boxShadow: <BoxShadow>[
          BoxShadow(
            color: Colors.black.withOpacity(0.11),
            blurRadius: 40,
            spreadRadius: 0,
          ),
        ],
      ),
      child: TextField(
        controller: _controller,
        onChanged: _filterPeaks,
        decoration: InputDecoration(
          filled: true,
          fillColor: Colors.white,
          contentPadding: const EdgeInsets.all(15),
          hintText: 'Gipfel suchen',
          prefixIcon: const Padding(
            padding: EdgeInsets.all(12),
            child: Icon(Icons.search),
          ),
          suffixIcon: IconButton(
            icon: const Icon(Icons.clear),
            onPressed: () {
              _controller.clear();
              _filterPeaks('');
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
}
