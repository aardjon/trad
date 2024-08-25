Table peaks {
  id integer [primary key]
  peak_name text [not null] 
}

Table routes {
  id integer [primary key]
  peak_id integer [ref: > peaks.id, not null]
  route_name text [not null]
  route_grade text [not null]
}

Table posts {
  id integer [primary key]
  route_id integer [ref: > routes.id, not null]
  user_name text [not null]
  post_date datetime [not null]
  comment text [not null]
  rating integer [not null]
}
