"""SQL utils."""
# pylint: disable=invalid-name
import os
import sqlite3
from typing import Iterable
import pypika

def dict_factory(cursor, row):
    """https://docs.python.org/3/library/sqlite3.html#sqlite3-howto-row-factory"""
    fields = [column[0] for column in cursor.description]
    return dict(zip(fields, row))

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
            self.conn.row_factory = dict_factory
            return self.conn.cursor()

        def __exit__(self, _type, value, traceback):
            self.conn.commit()
            self.conn.close()

    def __init__(self, path, *, create=False):
        if not create and not os.path.exists(path):
            raise ValueError(
                f"{path} does not exist and create is set to False.")
        self.path = path

    def execute(self, query):
        """Execute a query."""
        with Db.SQLite(self.path) as cursor:
            return cursor.execute(str(query)).fetchall() # Return results first...

    def list_tables(self):
        """List all tables present."""
        master = pypika.Table('sqlite_master')
        query = pypika.Query.select(master.name) \
                        .from_(master) \
                        .where(master.type == "table")
        with Db.SQLite(self.path) as cursor:
            return [row['name'] for row in cursor.execute(str(query)).fetchall()]

    def create_table(self, table: str, columns: Iterable[tuple], *,
                     primary_keys: Iterable[str] = (),
                     unique: Iterable[str] = ()):
        """Create a new table, if it doesn't exist already."""
        # https://github.com/kayak/pypika#creating-tables
        if table in self.list_tables():
            raise ValueError(f"{table} already exists.")
        query = pypika.Query.create_table(table) \
                            .columns(*[pypika.Column(*column)
                                       for column in columns])
        if len(primary_keys) > 0:
            query = query.primary_key(*primary_keys)
        if len(unique) > 0:
            query = query.unique(*unique)
        # IF NOT EXISTS is not supported here. Manually check.
        with Db.SQLite(self.path) as cursor:
            cursor.execute(str(query))

    def describe_table(self, table: str):
        """Describe the table format."""
        master = pypika.Table('sqlite_master')
        query = pypika.Query.select(master.sql) \
                        .from_(master) \
                        .where(master.name == table)
        with Db.SQLite(self.path) as cursor:
            return cursor.execute(str(query)).fetchone()['sql']

    def insert(self, table: str, values):
        """Insert one or more values into a table."""
        table = pypika.Table(table)
        query = pypika.Query.into(table).insert(*values)
        with Db.SQLite(self.path) as cursor:
            cursor.execute(str(query))

    def select_all(self, table:str):
        """Select all rows from a table."""
        table = pypika.Table(table)
        query = pypika.Query.select(table.star).from_(table)
        with Db.SQLite(self.path) as cursor:
            return cursor.execute(str(query)).fetchall()
