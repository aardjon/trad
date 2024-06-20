import os
import sqlite3
import unittest

class SQLiteDatabase():
    def __init__(self, database_file_path, schema_file_path):
        self._db_connection = sqlite3.connect(database_file_path)
        self._db_cursor = self._db_connection.cursor()
        self.init_tables(schema_file_path)

    def init_tables(self, schema_file_path):       
        with open(schema_file_path , 'r') as sql_file:
            sql_script = sql_file.read()        
        self._db_cursor.executescript(sql_script)
        self._db_connection.commit()      

    def __del__(self):
        if self._db_connection:
                self._db_connection.close()

class TestDatabase(unittest.TestCase):
    def setUp(self):
        self.db_connection = sqlite3.connect(':memory:')
        self.sql_folder_path = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            'sql')
        self.execute_sql_file('journal.init.sql')

    def tearDown(self):
        self.db_connection.close()

    def execute_sql_file(self, sql_file_name):
        sql_file_path = os.path.join(self.sql_folder_path, sql_file_name)
        with open(sql_file_path, 'r') as sql_file:
            sql_script = sql_file.read()
        
        cursor = self.db_connection.cursor()
        cursor.executescript(sql_script)
        self.db_connection.commit()

    def test_basic_journal_insert(self):
        self.execute_sql_file('journal.basic_insert.sql')
        cursor = self.db_connection.cursor()
        cursor.execute('SELECT * FROM view_journal')
        result = cursor.fetchall()
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 3)

    def test_team_insert_normal(self):
        self.execute_sql_file('journal.team_insert_normal.sql')
        cursor = self.db_connection.cursor()
        cursor.execute('SELECT name, position FROM team ORDER BY position')
        actual = cursor.fetchall()
        self.assertIsNotNone(actual)    
        expected = [('John Doe', 0), ('Jane Smith', 1), ('Alice Johnson', 2)]
        self.assertListEqual(actual, expected)     
     
    
if __name__ == '__main__':
    # unittest.main()
            
    script_path = os.path.dirname(os.path.realpath(__file__))
    sqlite_database = SQLiteDatabase(
        os.path.join(script_path, 'journal.sqlite'),
        os.path.join(script_path, 'sql', 'journal.init.sql'))