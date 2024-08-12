import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:teufelsturm_viewer/models/post_data.dart';
import 'package:teufelsturm_viewer/models/route_data.dart';
import 'package:teufelsturm_viewer/utils/posts_filter_mode.dart';
import 'package:teufelsturm_viewer/utils/rating_helper.dart';
import 'package:teufelsturm_viewer/utils/shared_preferences_manager.dart';
import 'package:teufelsturm_viewer/utils/sqlite_manager.dart';

class _PostItem extends StatelessWidget {
  final PostData post;

  const _PostItem({required this.post, super.key});

  @override
  Widget build(BuildContext context) {
    DateFormat formatter = DateFormat('dd.MM.yyyy HH:mm');
    String formattedDate = formatter.format(post.postDate);

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
                Text(
                  post.userName,
                  style: const TextStyle(fontWeight: FontWeight.bold),
                ),
                RatingHelper.getIntRatingIcon(post.rating),
              ],
            ),
            const SizedBox(height: 5),
            Text(formattedDate),
            const SizedBox(height: 5),
            Text(post.comment),
          ],
        ),
      ),
    );
  }
}

class RouteDetailsView extends StatefulWidget {
  final RouteData route;
  final SqliteManager sqliteManager;

  const RouteDetailsView({required this.route, required this.sqliteManager, super.key});

  @override
  State<RouteDetailsView> createState() => _RouteDetailsViewState();
}

class _RouteDetailsViewState extends State<RouteDetailsView> {
  List<PostData> _posts = <PostData>[];
  PostsFilterMode _postsFilterMode = PostsFilterMode.newestFirst;
  final SharedPreferencesManager _sharedPreferencesManager = SharedPreferencesManager();

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: _appBar(),
      body: _listView(),
    );
  }

  @override
  void initState() {
    super.initState();

    Future.wait(<Future<void>>[_loadPostsFilterMode(), _loadPostsFromDatabase()]).then((_) {
      _sortPosts();
    });
  }

  AppBar _appBar() {
    String routeName = widget.route.routeName;
    String routeGrade = widget.route.routeGrade;

    return AppBar(
      title: Column(
        children: <Widget>[
          Text(
            routeName,
            style: const TextStyle(fontSize: 20),
          ),
          Text(
            routeGrade,
            style: const TextStyle(fontSize: 14),
          ),
        ],
      ),
      centerTitle: true,
      backgroundColor: Colors.lightGreen,
      actions: <Widget>[
        IconButton(
          onPressed: _showFilterOptions,
          icon: const Icon(Icons.filter_list),
        ),
      ],
    );
  }

  ListTile _createFilterMenuItem(
    BuildContext context,
    PostsFilterMode postsFilterMode,
    String title,
  ) {
    return ListTile(
      title: Text(title),
      trailing: _postsFilterMode == postsFilterMode ? const Icon(Icons.done) : const Icon(null),
      onTap: () {
        _setFilter(postsFilterMode);
        Navigator.pop(context);
      },
    );
  }

  ListView _listView() {
    return ListView.builder(
      itemCount: _posts.length,
      itemBuilder: (BuildContext context, int index) {
        return _PostItem(post: _posts[index]);
      },
    );
  }

  Future<void> _loadPostsFilterMode() async {
    _postsFilterMode = await _sharedPreferencesManager.getEnum<PostsFilterMode>(
          'postsFilterMode',
          PostsFilterMode.values,
        ) ??
        _postsFilterMode;
  }

  Future<void> _loadPostsFromDatabase() async {
    List<PostData> posts = await widget.sqliteManager.getAllPosts(
      widget.route.id,
    );
    setState(() {
      _posts = posts;
    });
  }

  Future<bool> _savePostsFilterMode() async {
    return await _sharedPreferencesManager.setEnum(
      'postsFilterMode',
      _postsFilterMode,
    );
  }

  void _setFilter(PostsFilterMode postsFilterMode) {
    _postsFilterMode = postsFilterMode;
    _savePostsFilterMode();
    _sortPosts();
  }

  void _showFilterOptions() {
    showModalBottomSheet(
      context: context,
      builder: (BuildContext context) {
        return Column(
          mainAxisSize: MainAxisSize.min,
          children: <Widget>[
            _createFilterMenuItem(context, PostsFilterMode.newestFirst, 'Neuste zuerst'),
            _createFilterMenuItem(context, PostsFilterMode.oldestFirst, 'Älteste zuerst'),
          ],
        );
      },
    );
  }

  void _sortPosts() {
    final Map<PostsFilterMode, Function> sortFunction = <PostsFilterMode, Function>{
      PostsFilterMode.newestFirst: () => _posts.sortByDateNewestFirst(),
      PostsFilterMode.oldestFirst: () => _posts.sortByDateOldestFirst(),
    };

    setState(() {
      sortFunction[_postsFilterMode]?.call();
    });
  }
}
