CREATE TABLE IF NOT EXISTS database_metadata 
	(id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, 
	 schema_version_major INTEGER NOT NULL,
	 schema_version_minor INTEGER NOT NULL,
	 compile_time TEXT NOT NULL,
	 vendor TEXT NOT NULL);

CREATE TABLE IF NOT EXISTS summits 
	(id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, 
	 summit_name TEXT NOT NULL UNIQUE,
	 latitude INTEGER NOT NULL,
	 longitude INTEGER NOT NULL);
	 
CREATE INDEX IdxSummitId ON summits (id);
CREATE INDEX IdxSummitName ON summits (summit_name);	

CREATE TABLE IF NOT EXISTS routes 
	(id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	 summit_id INTEGER NOT NULL,
	 route_name TEXT NOT NULL,
	 route_grade TEXT NOT NULL,
	 danger BOOLEAN NOT NULL DEFAULT 0,
	 stars INTEGER NOT NULL DEFAULT 0,
	 grade_af INTEGER NOT NULL DEFAULT 0,
	 grade_rp INTEGER NOT NULL DEFAULT 0,
	 grade_ou INTEGER NOT NULL DEFAULT 0,
	 grade_jump INTEGER NOT NULL DEFAULT 0,
	 UNIQUE(summit_id,route_name,route_grade),
	 FOREIGN KEY(summit_id) REFERENCES summits (id) ON DELETE CASCADE);
	 
CREATE INDEX IdxRouteId ON routes (id);
CREATE INDEX IdxRouteName ON routes (route_name);

CREATE TABLE IF NOT EXISTS posts
	(id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	 route_id INTEGER NOT NULL,
	 user_name TEXT NOT NULL,
	 post_date TEXT NOT NULL,
	 comment TEXT NOT NULL,
     rating INTEGER NOT NULL,
     FOREIGN KEY(route_id) REFERENCES routes (id) ON DELETE CASCADE);	
	 
ANALYZE;
