///
/// Definition of the [Posting] entity class.
///
library;

/// A single posting.
///
/// Postings are written by community members and can be assigned e.g. to routes, allowing the
/// community to rate and comment. There can be multiple postings for the same entity.
class Posting {
  /// Name of the posting's author.
  String userName;

  /// The time the posting was published.
  DateTime postDate;

  /// The comment.
  String comment;

  /// The rating the author assigned to the entity this posting corresponds to.
  int rating;

  /// Constructor for directly initializing all members.
  Posting(this.userName, this.postDate, this.comment, this.rating);
}
