"""Tests for SqlUtils."""
# pylint: disable=invalid-name

import unittest
import tempfile
from src.sql_utils import Db

CREATE_DB_IF_NOT_PRESENT = True
class TestSqlUtils(unittest.TestCase):
    """Tests for SqlUtils"""

    def test_create_table(self):
        """Test Create Table."""
        with tempfile.TemporaryDirectory() as tempdirname:
            db = Db(f"{tempdirname}/test.db", CREATE_DB_IF_NOT_PRESENT)
            db.create_table("Vehicle", (("id", "INTEGER"),
                                        ("make", "TEXT"),
                                        ("model", "TEXT"),
                                        ("miles", "INTEGER")))
            self.assertEqual(len(db.list_tables()), 1)

        with tempfile.TemporaryDirectory() as tempdirname:
            db = Db(f"{tempdirname}/test.db", CREATE_DB_IF_NOT_PRESENT)
            db.create_table("Vehicle", (("id", "INTEGER"),
                                        ("make", "TEXT"),
                                        ("model", "TEXT", False),
                                        ("miles", "INTEGER", True)),
                                        primary_keys=("id",),
                                        unique=("make",))
            self.assertEqual(len(db.list_tables()), 1)

    def test_list_tables(self):
        """Test List Tables"""
        with tempfile.TemporaryDirectory() as tempdirname:
            db = Db(f"{tempdirname}/test.db", CREATE_DB_IF_NOT_PRESENT)
            db.create_table("Vehicle", (("id", "INTEGER"),))
            db.create_table("Person", (("id", "INTEGER"),))
            db.create_table("Country", (("id", "INTEGER"),))
            self.assertEqual(set(db.list_tables()), {"Vehicle", "Person", "Country"})

    def test_describe_table(self):
        """Test Describe Tables"""
        with tempfile.TemporaryDirectory() as tempdirname:
            db = Db(f"{tempdirname}/test.db", CREATE_DB_IF_NOT_PRESENT)
            db.create_table("Vehicle", (("id", "INTEGER"),
                                        ("make", "TEXT"),
                                        ("model", "TEXT"),
                                        ("miles", "INTEGER")))
            result = db.describe_table("Vehicle")
            self.assertEqual(result, ('CREATE TABLE "Vehicle" '
                                      '("id" INTEGER,"make" TEXT,"model" TEXT,"miles" INTEGER)'))

    def test_insert(self):
        """Test Insert"""
        with tempfile.TemporaryDirectory() as tempdirname:
            db = Db(f"{tempdirname}/test.db", CREATE_DB_IF_NOT_PRESENT)
            db.create_table("Person", (("name", "STRING"), ("age", "INTEGER")))
            db.insert("Person", (("Chip", 33), ("Melinda", 34)))
            self.assertSetEqual(
                {(row['name'], row['age']) for row in db.select_all("Person")},
                {("Chip", 33), ("Melinda", 34)})
