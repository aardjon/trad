Table peaks {
  id integer [primary key]
  peak_name text  
}

Table routes {
  id integer [primary key]
  peak_id integer [ref: > peaks.id]
  route_name text
}

Table posts {
  id integer [primary key]
  route_id integer [ref: > routes.id]
  user_name text
  post_date datetime
  comment text
  rating integer
}