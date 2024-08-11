///
/// Definition of the [Post] entity class.
///
library;

/// A single post someone contributed to a public climbing database or community.
///
/// Posts are written by community members and can be assigned e.g. to routes, allowing the
/// community to rate and comment. There can be multiple posts for the same entity.
class Post {
  /// Name of the post's author.
  String userName;

  /// The time the post was published.
  DateTime postDate;

  /// The comment.
  String comment;

  /// The rating the author assigned to the entity this post corresponds to.
  int rating;

  /// Constructor for directly initializing all members.
  Post(this.userName, this.postDate, this.comment, this.rating);
}
