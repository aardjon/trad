Project RouteDb {
  Note: '''
  # Schema of the Route Database

  The route database is a single SQLite file with the schema documented here. You can create a
  graphical view of the database schema from this document at: https://dbdiagram.io
  '''

  // The schema version uses semantic versioning (https://semver.org/) without the PATCH level.
  schema_version: "1.2"

  // Unique constraints that stretch over multiple columns are not supported by DBML yet
  // (https://github.com/holistics/dbml/issues/68). So we use this workaround instead: The property
  // with this special name is a JSON dictionary mapping a list of constraints (each being the list
  // of column names) to the table name.
  composite_unique_constraints:
    '''
    {
        "routes": [
            ["summit_id", "route_name", "route_grade"]
        ],
        "database_metadata": [
            ["schema_version_major", "schema_version_minor", "compile_time", "vendor", "compiler"]
        ]
    }
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
  
  compiler text [
    not null,
    note: '''
    Identifying label (e.g. name and version) of the compiler used to create this database.
    '''
  ]
}


Table external_data_sources {
  Note: '''
  References to all external sources the data contained in this route DB was extracted from.
  '''
  
  id integer [
    primary key,
    increment,
    note: 'Unique ID of this data source.'
  ]
  label text [
    not null,
    unique,
    note: 'Display name of this data source.'
  ]
  url text [
    not null,
    note: '''
      Landing page URL (not an API endpoint!) a user may visit by browser to get further
      information about this data source.
    '''
  ]
  attribution text [
    not null,
    note: 'Attribution string (e.g. author names) for the data from this source.'
  ]
  license text [
    null,
    note: '''
      Short, human-readable name of the licence which applies to all data from this source.
      Using an abbreviation or SPDX identifier (e.g. "CC-BY-4.0" or "ODbL") instead of a longer
      licence name is preferred. May be NULL if the license is unknown or doesn't apply.
    '''
  ]
}


Table areas {
  Note: '''
  All climbing areas/sectors.
  
  An area or sector is a geographic area containing several summits. Each summit is assigned to
  one.
  '''
  
  id integer [
    primary key,
    increment,
    note: 'Unique ID of this area/sector.'
  ]

  name text [
    not null,
    unique,
    note: 'Name of this area/sector.'
  ]
  
  indexes {
    name [name: 'IdxAreaName']
  }
}


Table summit_names {
  Note: '''
  All names of all summits.
  
  As a single summit can have multiple names, this table assigns specific names strings to summits.
  Each summit must have exactly one official name assigned, but there may be several (including no)
  additional names as well.

  This table is designed for both searching by name and retrieving the name(s) of summits.
  '''

  name text [
    not null,
    note: 'A single summit name string.'
  ]
  usage integer [
    not null,
    note: '''
      Usage of this name string (for this summit):
      0 = Official name (the name given and used by local authorities, usually the default)
      1 = Alternate name (e.g. a well-known "nickname" or an old name)
    '''
  ]
  summit_id integer [
    not null,
    note: 'ID of the summit this name is assigned to.'
  ]

  indexes {
    (summit_id, usage, name) [pk]
    name [name: 'IdxSummitName']
  }
}
// Foreign key summit_names -> summits
Ref: summits.id < summit_names.summit_id [delete: cascade]

 
Table summits {
  Note: '''
  Table containing all summit data.
  
  The summit names are stored in the `summit_names` table. Each summit is guaranteed to have
  exactly one official name assigned.
  
  To store geographical coordinate values as integer values, their decimal representation is
  multiplied by 10.000.000 to support the same precision as the OSM database (7 decimal places,
  ~1 cm). Positive values are N/E, negative ones are S/W. For example, (50,9170936, 14,1992389) is
  stored as (509170936, 141992389).

  See also: https://wiki.openstreetmap.org/wiki/Precision_of_coordinates
  '''

  id integer [
    primary key,
    increment,
    note: 'Summit ID, unique within this database.'
  ]
  
  area_id integer [
    not null,
    note: 'ID of the area/sector this summit belongs to.'
  ]

  latitude integer [
    not null,
    note: 'The latitude value of the geographical position.'
  ]

  longitude integer [
    not null,
    note: 'The longitude value of the geographical position.'
  ]
}
// Foreign key summits -> areas
Ref: areas.id < summits.area_id [delete: cascade]


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
    style. This is the main style which is always set as long as there is a climb at all. Set to 0
    for pure jump routes.
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
    The count of official stars assigned to this route. An increasing number of stars marks a
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
  
  source_id integer [
    not null,
    note: 'ID of the external data source this post originates from.'
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
// Foreign key posts -> external_data_sources
Ref: external_data_sources.id < posts.source_id [delete: cascade]
