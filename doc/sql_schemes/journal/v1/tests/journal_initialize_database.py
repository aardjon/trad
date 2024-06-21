import os
import sqlite3

class SQLiteDatabase():
    def __init__(self, database_file_path, schema_file_path):
        self._db_connection = sqlite3.connect(database_file_path)
        self._db_cursor = self._db_connection.cursor()
        self.init_tables(schema_file_path)

    def init_tables(self, schema_file_path):       
        with open(schema_file_path , 'r', encoding='utf-8') as sql_file:
            sql_script = sql_file.read()        
        self._db_cursor.executescript(sql_script)
        self._db_connection.commit()      

    def __del__(self):
        if self._db_connection:
                self._db_connection.close()
     
    
if __name__ == '__main__':                
    script_path = os.path.dirname(os.path.realpath(__file__))

    database_file_path = os.path.join(script_path, 'journal.sqlite')

    schema_file_path = os.path.abspath(
         os.path.join(script_path, os.pardir,
                      'v1.journal.initialize_database.sql'))

    sqlite_database = SQLiteDatabase(database_file_path, schema_file_path)