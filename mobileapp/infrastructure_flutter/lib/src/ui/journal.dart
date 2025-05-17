///
/// Provides the *Journal* page widget.
///
library;

import 'package:flutter/material.dart';

/// Widget representing the *Journal* page.
///
// TODO(aardjon): This is only a stub for now.
class JournalPage extends StatelessWidget {
  /// The app drawer (navigation menu) to use.
  final Widget _appDrawer;

  /// The page title
  final String _title;

  /// Constructor for directly initializing all members.
  const JournalPage(this._appDrawer, this._title, {super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        backgroundColor: Theme.of(context).colorScheme.inversePrimary,
        title: Text(_title),
      ),
      body: const Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: <Widget>[Text('This is the Journal Page')],
        ),
      ),
      drawer: _appDrawer,
    );
  }
}
