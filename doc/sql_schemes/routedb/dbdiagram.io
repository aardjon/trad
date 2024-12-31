Table database_metadata {
  schema_version_major integer [not null]
  schema_version_minor integer [not null]
  compile_time text [not null]
  vendor text [not null]
}

Table summits {
  id integer [primary key]
  summit_name text [not null]
  latitude INTEGER [not null]
  longitude INTEGER [not null]
}

Table routes {
  id integer [primary key]
  summit_id integer [ref: > summits.id, not null]
  route_name text [not null]
  route_grade text [not null]
  grade_af integer [not null]
  grade_rp integer [not null]
  grade_ou integer [not null]
  grade_jump integer [not null]
  stars integer [not null]
  danger boolean [not null]
}

Table posts {
  id integer [primary key]
  route_id integer [ref: > routes.id, not null]
  user_name text [not null]
  post_date datetime [not null]
  comment text [not null]
  rating integer [not null]
}
