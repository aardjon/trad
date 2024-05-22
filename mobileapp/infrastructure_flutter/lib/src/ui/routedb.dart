///
/// Provides the *Route DB* page widget.
///
library;

import 'package:flutter/material.dart';

/// Widget representing the *Route DB* page.
///
/// TODO: This is only a stub for now.
class RouteDbPage extends StatelessWidget {
  /// The app drawer (navigation menu) to use.
  final NavigationDrawer _appDrawer;

  /// The page title
  final String _title;

  const RouteDbPage(this._appDrawer, this._title, {super.key});

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
          children: <Widget>[
            Text(
              'This is the RouteDb Page',
            ),
          ],
        ),
      ),
      drawer: _appDrawer,
    );
  }
}
