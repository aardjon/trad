import os
import sqlite3
import unittest

class TestDatabase(unittest.TestCase):
    def setUp(self):
        self.db_connection = sqlite3.connect(':memory:')
        self.db_connection.execute('PRAGMA foreign_keys = ON')
        self.tests_folder_path = os.path.dirname(os.path.realpath(__file__))
        self.execute_sql_file('../v1.journal.initialize_database.sql')

    def tearDown(self):
        self.db_connection.close()

    def execute_sql_file(self, sql_file_name):
        sql_file_path = os.path.join(self.tests_folder_path, sql_file_name)
        with open(sql_file_path, 'r', encoding='utf-8') as sql_file:
            sql_script = sql_file.read()
        
        cursor = self.db_connection.cursor()
        cursor.executescript(sql_script)
        self.db_connection.commit()

    def test_basic_insert(self):
        self.execute_sql_file('basic_insert.sql')
        cursor = self.db_connection.cursor()

        cursor.execute('SELECT * FROM view_journal')
        actual_journal = cursor.fetchall()
        self.assertIsNotNone(actual_journal)
        expected_journal = [
            (1, '2024-06-14', 'Bielatal', 'Glasergrundwand', 'Südkante', 'II', None, None),
            (2, '2024-06-15', 'Bielatal', 'Glasergrundwand', 'Rechter Schartenriß', 'III', 'E2', None),
            (3, '2024-06-16', 'Bielatal', 'Glasergrundwand', 'Südostkamin', 'I', 'E3', 'Man kann nicht wirklich rausfallen')
        ]        
        self.assertListEqual(actual_journal, expected_journal)

        cursor.execute('SELECT * FROM team')
        actual_team = cursor.fetchall()
        self.assertIsNotNone(actual_journal)
        expected_team = [
            (1, 1, 'John Doe', 0),
            (2, 1, 'Jane Smith', 1),
            (3, 1, 'Alice Johnson', 2)
        ]        
        self.assertListEqual(actual_team, expected_team)

    def test_delete_log(self):
        self.execute_sql_file('basic_insert.sql')
        self.execute_sql_file('delete_log.sql')
        cursor = self.db_connection.cursor()

        cursor.execute('SELECT * FROM view_journal')
        actual_journal = cursor.fetchall()
        self.assertIsNotNone(actual_journal)
        expected_journal = [            
            (2, '2024-06-15', 'Bielatal', 'Glasergrundwand', 'Rechter Schartenriß', 'III', 'E2', None),
            (3, '2024-06-16', 'Bielatal', 'Glasergrundwand', 'Südostkamin', 'I', 'E3', 'Man kann nicht wirklich rausfallen')
        ]        
        self.assertListEqual(actual_journal, expected_journal)

        cursor.execute('SELECT * FROM team')
        actual_team = cursor.fetchall()
        self.assertIsNotNone(actual_journal)
        expected_team = []        
        self.assertListEqual(actual_team, expected_team)
     
    
if __name__ == '__main__':
    unittest.main()        