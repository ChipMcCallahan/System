"""SQL utils."""
# pylint: disable=invalid-name
import os
import sqlite3
from versatuple import versatuple

Table = versatuple("Table", ("name", "columns"))

Column = versatuple("Column", ("name", "type", "is_key"))



class Db:
    """Utility class for working with SQLite databases."""

    class SQLite:
        """SQLite Wrapper supporting auto-commit and auto-close. 
        https://stackoverflow.com/questions/19522505/using-sqlite3-in-python-with-with-keyword"""
        def __init__(self, file):
            self.file=file
            self.conn=None
        def __enter__(self):
            self.conn = sqlite3.connect(self.file)
            return self.conn.cursor()
        def __exit__(self, _type, value, traceback):
            self.conn.commit()
            self.conn.close()

    def __init__(self, path, create=False):
        if not create and not os.path.exists(path):
            raise ValueError(f"{path} does not exist and create is set to False.")
        self.path = path

    def create_table(self, table):
        """Create a new table."""
        # https://www.sqlitetutorial.net/sqlite-create-table/
        with Db.SQLite(self.path) as cursor:
            cursor.execute(self.create_table_query(table))

    @staticmethod
    def create_table_query(table):
        """Returns a CREATE TABLE query for this table object."""
        lines = (',\n').join([f"    {col.name} {col.type}{' PRIMARY KEY' if col.is_key else ''}"
                 for i, col in enumerate(table.columns)])
        return f"CREATE TABLE IF NOT EXISTS {table.name}(\n{lines}) WITHOUT ROWID;"
