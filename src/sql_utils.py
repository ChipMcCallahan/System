"""SQL utils."""
# pylint: disable=invalid-name
import os
import sqlite3
import pypika
from versatuple import versatuple

Table = versatuple("Table", ("name", "columns"))

Column = versatuple("Column", ("name", "type", "is_key"))


class Db:
    """Utility class for working with SQLite databases."""

    class SQLite:
        """SQLite Wrapper supporting auto-commit and auto-close. 
        https://stackoverflow.com/questions/19522505/using-sqlite3-in-python-with-with-keyword"""

        def __init__(self, file):
            self.file = file
            self.conn = None

        def __enter__(self):
            self.conn = sqlite3.connect(self.file)
            return self.conn.cursor()

        def __exit__(self, _type, value, traceback):
            self.conn.commit()
            self.conn.close()

    def __init__(self, path, create=False):
        if not create and not os.path.exists(path):
            raise ValueError(
                f"{path} does not exist and create is set to False.")
        self.path = path

    def execute(self, query):
        """Execute a query."""
        with Db.SQLite(self.path) as cursor:
            return cursor.execute(str(query))

    def create_table(self, table):
        """Create a new table."""
        # https://www.sqlitetutorial.net/sqlite-create-table/
        # https://github.com/kayak/pypika#creating-tables
        query_columns = [pypika.Column(c.name, c.type) for c in table.columns]
        query = pypika.Query.create_table(table.name).columns(*query_columns)
        for c in table.columns:
            if c.is_key:
                query = query.primary_key(c.name)
        self.execute(query)
