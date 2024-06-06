///
/// Provides the *knowledge base* page widget.
///
library;

import 'package:flutter/material.dart';
import 'package:flutter_markdown/flutter_markdown.dart';

import 'package:adapters/boundaries/ui.dart';
import 'package:adapters/controllers.dart';

/// View representing the *knowledge base* page.
///
/// This widget displays the Markdown document provided by the route. For rendering Markdown text,
/// the `Markdown` widget from the `flutter_markdown` library is used.
class KnowledgebaseView extends StatelessWidget {
  /// The app drawer (navigation menu) to use.
  final NavigationDrawer _appDrawer;

  /// The page title
  final String _title;

  /// Controller to notify about user actions.
  final KnowledgebaseController _controller;

  /// Constructor for directly initializing all members.
  KnowledgebaseView(this._appDrawer, this._title, {super.key})
      : _controller = KnowledgebaseController();

  @override
  Widget build(BuildContext context) {
    final KnowledgebaseModel model =
        ModalRoute.of(context)!.settings.arguments as KnowledgebaseModel;
    return Scaffold(
      appBar: AppBar(
        backgroundColor: Theme.of(context).colorScheme.inversePrimary,
        title: Text(model.documentTitle),
      ),
      body: Center(
        child: Markdown(
          data: model.documentContent,
          onTapLink: (String text, String? href, String title) {
            _controller.requestShowDocument(href!);
          },
        ),
      ),
      drawer: _appDrawer,
    );
  }
}
