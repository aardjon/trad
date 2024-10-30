import sqlite3

class Database():
    def __init__(self, database_file_path, schema_file_path):
        self._db_connection = sqlite3.connect(database_file_path)
        self._db_cursor = self._db_connection.cursor()
        self.init_tables(schema_file_path)

    def init_tables(self, schema_file_path):
        query = "SELECT name from sqlite_master WHERE type='table' AND name='peaks';"        
        self._db_cursor.execute(query)
        result = self._db_cursor.fetchone()
        if result != None:
            return
        
        with open(schema_file_path , 'r') as sql_file:
            sql_script = sql_file.read()        
        self._db_cursor.executescript(sql_script)
        self._db_connection.commit()      

    def insert_peak(self, peak_name):
        self._db_cursor.execute("INSERT OR IGNORE INTO peaks (peak_name) VALUES (?)", (peak_name,))
        self._db_cursor.execute("SELECT id FROM peaks WHERE peak_name = ?", (peak_name,))
        return self._db_cursor.fetchone()[0]

    def insert_route(self, peak_id, route_name, route_grade):
        self._db_cursor.execute("INSERT OR IGNORE INTO routes (peak_id,route_name,route_grade) VALUES (?,?,?)", (peak_id,route_name,route_grade,))
        self._db_cursor.execute("SELECT id FROM routes WHERE peak_id = ? AND route_name = ?", (peak_id,route_name,))
        return self._db_cursor.fetchone()[0]

    def insert_posts(self, route_id, posts):
        for post in posts:
            self._db_cursor.execute("INSERT OR IGNORE INTO posts (route_id,user_name,post_date,comment,rating) VALUES (?,?,?,?,?)", (route_id,post.user_name,post.post_date,post.comment,post.rating))                        

    def save_to_sqlite(self, page_data):
        try:
            peak_id = self.insert_peak(page_data.peak)
            route_id = self.insert_route(peak_id, page_data.route, page_data.grade)      
            self.insert_posts(route_id, page_data.posts)
        except:
            raise Exception("Error while saving to sqlite")
        self._db_connection.commit()

    def __del__(self):
        if self._db_connection:
                self._db_connection.close()