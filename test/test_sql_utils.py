"""Tests for SqlUtils."""
# pylint: disable=invalid-name

import unittest
import sqlite3
import tempfile
from src.sql_utils import Db

class TestSqlUtils(unittest.TestCase):
    """Tests for SqlUtils"""

    def test_create(self):
        """Test Create Table."""
        with tempfile.TemporaryDirectory() as tempdirname:
            db = Db(f"{tempdirname}/test.db", create=True)
            db.create("Vehicle", "id INTEGER PRIMARY KEY", "make TEXT NOT NULL",
                                 "model TEXT UNIQUE", "miles INTEGER")
            self.assertEqual(len(db.list()), 1)

    def test_list(self):
        """Test List Tables"""
        with tempfile.TemporaryDirectory() as tempdirname:
            db = Db(f"{tempdirname}/test.db", create=True)
            db.create("Vehicle", "id INTEGER PRIMARY KEY")
            db.create("Person", "id INTEGER PRIMARY KEY")
            db.create("Country", "id INTEGER PRIMARY KEY")
            self.assertEqual(set(db.list()), {"Vehicle", "Person", "Country"})

    def test_describe(self):
        """Test Describe Tables"""
        with tempfile.TemporaryDirectory() as tempdirname:
            db = Db(f"{tempdirname}/test.db", create=True)
            db.create("Vehicle", "id INTEGER PRIMARY KEY", "make TEXT NOT NULL",
                                 "model TEXT UNIQUE", "miles INTEGER")
            result = db.describe("Vehicle")
            self.assertEqual(result, ('CREATE TABLE Vehicle(id INTEGER PRIMARY KEY,'
                                      'make TEXT NOT NULL,'
                                      'model TEXT UNIQUE,'
                                      'miles INTEGER) WITHOUT ROWID'))

    def test_insert(self):
        """Test Insert"""
        with tempfile.TemporaryDirectory() as tempdirname:
            db = Db(f"{tempdirname}/test.db", create=True)
            db.create("Person", "name TEXT PRIMARY KEY", "age INTEGER")
            db.put("Person", ("Chip", 33), ("Melinda", 34))
            self.assertEqual(db.all("Person"),
                [{"name": "Chip", "age": 33}, {"name": "Melinda", "age": 34}])

    def test_pk_unique_notnull(self):
        """Test PRIMARY KEY, UNIQUE, and NOT NULL enforced"""
        with tempfile.TemporaryDirectory() as tempdirname:
            db = Db(f"{tempdirname}/test.db", create=True)
            db.create("Person", "name TEXT PRIMARY KEY", "age INTEGER UNIQUE",
                                "id INTEGER NOT NULL")
            db.put("Person", ("Joshua", 34, 1))
            with self.assertRaises(sqlite3.IntegrityError):
                db.put("Person", ("Joshua", 35, 1))
            with self.assertRaises(sqlite3.IntegrityError):
                db.put("Person", ("Jessica", 34, 1))
            with self.assertRaises(sqlite3.IntegrityError):
                db.run("INSERT INTO Person(name, age) VALUES ('Jessica', 35)")
