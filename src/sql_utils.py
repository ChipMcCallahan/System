"""Personal SQL utils. NOT SQL injection safe."""
# pylint: disable=invalid-name
import os
import sqlite3

def dict_factory(cursor, row):
    """https://docs.python.org/3/library/sqlite3.html#sqlite3-howto-row-factory"""
    fields = [column[0] for column in cursor.description]
    return dict(zip(fields, row))

class Db:
    """Utility class for working with SQLite databases. NOT SQL Injection safe!"""

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

    def run(self, query):
        """Run a query."""
        with Db.SQLite(self.path) as cursor:
            return cursor.execute(str(query)).fetchall()

    def create(self, table, *columns):
        """Create a table."""
        query = f"CREATE TABLE IF NOT EXISTS {table}({','.join(columns)}) WITHOUT ROWID;"
        self.run(query)

    def list(self):
        """List all tables present."""
        query = "SELECT name FROM sqlite_master WHERE type = 'table'"
        return [t['name'] for t in self.run(query)]

    def describe(self, table: str):
        """Describe the table format."""
        query = f"SELECT sql FROM sqlite_master WHERE name = '{table}'"
        return self.run(query)[0]['sql']

    def put(self, table: str, *values):
        """Insert one or more values into a table."""
        query = f"INSERT INTO {table} VALUES {','.join(str(v) for v in values)}"
        self.run(query)

    def all(self, table:str):
        """Select all rows from a table."""
        return self.run(f"SELECT * FROM {table}")

    def rename(self, table: str, name: str):
        """Rename a table."""
        self.run(f"ALTER TABLE {table} RENAME TO {name}")
