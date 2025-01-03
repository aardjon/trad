Project RouteDb {
  Note: '''
  # Schema of the Route Database

  The route database is a single SQLite file with the schema documented here. You can create a
  graphical view of the database schema from this document at: https://dbdiagram.io

  Schema Version: 1.0

  The schema version uses semantic versioning (https://semver.org/) without the PATCH level.
  '''
}


Table database_metadata {
  Note: '''
  Table containing some static metadata about the database itself.
  
  Must contain exactly one row.
  '''

  schema_version_major integer [
    not null,
    note:'Major part of the schema version (corresponding to incompatible changes).'
  ]

  schema_version_minor integer [
    not null,
    note: 'Minor part of the schema version (corresponding to backward-compatible changes).']

  compile_time text [
    not null,
    note: '''
    Date and time this database has been created.
    
    This is an ISO 8601 string value (i.e. something like "YYYY-MM-DDTHH:MM:SS.ffffff+HH:MM")
    and must include proper time zone information.
    '''
  ]

  vendor text [
    not null,
    note: '''
    Vendor identification label of the database provider.
    This is an arbitrary (even empty) display string to distinguish different database sources.
    '''
  ]
}

 
Table summits {
  Note: '''
  Table containing all summits.
  
  Summit data from different sources is usually merged based on the summit name. To store
  geographical coordinate values as integer values, their decimal representation is multiplied by
  10.000.000 to support the same precision as the OSM database (7 decimal places, ~1 cm). Positive
  values are N/E, negative ones are S/W. For example, (50,9170936, 14,1992389) is stored as
  (509170936, 141992389).

  See also: https://wiki.openstreetmap.org/wiki/Precision_of_coordinates
  '''

  id integer [
    primary key,
    increment,
    note: 'Summit ID, unique within this database.'
  ]

  summit_name text [
    not null,
    unique,
    note: 'Official name of this summit. Names are unique.'
  ]

  latitude INTEGER [
    not null,
    note: 'The latitude value of the geographical position.'
  ]

  longitude INTEGER [
    not null,
    note: 'The longitude value of the geographical position.'
  ]

  indexes {
    summit_name [name: 'IdxSummitName']
  }
}


Table routes {
  Note: '''
  Table containing all routes.

  Route names are unique for each summit, therefore route data from different sources can be
  merged based on the (summit, route name) combination.

  Routes have several grades describing their difficulty, depending on the route characteristics
  (e.g. does it include a jump?), the climbing style (e.g. "all free" or "redpoint") and also on
  each other:
   - A route without a jumping grade is usually climbed without having to jump
   - A route with both grades contains a single jump within its climbing parts
   - A route with only a jumping grade consists of a single jump only
   - The AF/RP ratings of a route with OU grade require some additional support

  Grades are represented by integer numbers, with 1 being the lowest (or "easiest") possible
  rating and without an upper bound. Each step in the corresponding scale system increases the
  value by one, so e.g. the saxon grade VIIb is stored as 8 and the UIAA grade IV is stored as 6.
  0 can be used when a certain grade doesn't apply to a route at all, e.g. when there is no jump.
  '''

  id integer [
    primary key,
    increment,
    note: 'Route ID, unique within this database.'
  ]

  summit_id integer [
    not null,
    note: 'ID of the summit this route is assigned to. Foreign key to the summits table.'
  ]

  route_name text [
    not null,
    note: '''
    Name of this route. Unique within this summit, but different summits may have routes with
    identical names (e.g. "AW").
    '''
  ]

  route_grade text [
    not null,
    note: 'Grade label. Deprecated, please use the more fine-grained grade columns instead.'
  ]

  grade_af integer [
    not null,
    note: '''
    The grade that applies when climbing this route in the AF ("alles frei", i.e. "all free")
    style, i.e. without any belaying (no rope, no abseiling). Set to 0 when it is just a single
    jump.
    '''
  ]

  grade_rp integer [
    not null,
    note: '''
    The grade that applies when climbing this route in the RP ("Rotpunkt", i.e. "redpoint")
    style. Set to 0 when it is just a single jump.
    '''
  ]

  grade_ou integer [
    not null,
    note: '''
    The grade that applies when climbing this route in the OU ("ohne Unterstützung", i.e.
    "without support") style, i.e. without using the support considered in the AF style
    grade. Set to 0 when the AF grade doesn't include any support.
    '''
  ]

  grade_jump integer [
    not null,
    note: 'The grade of the jump within this route. Set to 0 when there is no need to jump.'
  ]

  stars integer [
    not null,
    note: '''
    The count of official stars assigend to this route. An increasing number of stars marks a
    route as "more beautiful". 0 is the default for regular routes.
    '''
  ]

  danger boolean [
    not null,
    note: 'True if the route is officially marked as "dangerous", false if not.'
  ]

  indexes {
    route_name [name: 'IdxRouteName']
  }
  
  // Unique constraint which I don't know how to define here yet:
  // UNIQUE(summit_id, route_name, route_grade)
}
// Foreign key routes -> summits
Ref: summits.id < routes.summit_id [delete: cascade]


Table posts {
  Note: 'Table containing all posts that have been assigned to routes.'

  id integer [
    primary key,
    increment,
    note: 'Post ID, unique within this database.'
  ]

  route_id integer [
    not null,
    note: 'ID of the route this post is assigned to. Foreign key to the routes table.'
  ]

  user_name text [
    not null,
    note: "Name of the post's author."
  ]

  post_date text [
    not null,
    note: '''
    The date and time the post was published. ISO 8601 string value
    ("YYYY-MM-DDTHH:MM:SS.ffffff+HH:MM").
    '''
  ]

  comment text [
    not null,
    note: 'The comment.'
  ]

  rating integer [
    not null,
    note: '''
    The rating the author assigned to the route this post corresponds to. This is a signed integer
    value in the range between -3 (extremely bad/dangerous) to 3 (extremely outstanding/great).
    '''
  ]
}
// Foreign key posts -> routes
Ref: routes.id < posts.route_id [delete: cascade]
