"""Tests for SqlUtils."""
# pylint: disable=invalid-name

import os
import unittest
import tempfile
from src.sql_utils import Column, Table, Db

class TestSqlUtils(unittest.TestCase):
    """Tests for SqlUtils"""

    def test_create_table(self):
        """Test Create Table."""
        columns = (
            Column.new().Name("id").Type("INTEGER").Is_key(True),
            Column.new().Name("make").Type("TEXT"),
            Column.new().Name("model").Type("TEXT"),
            Column.new().Name("miles").Type("INTEGER")
        )
        table = Table.new().Name("Vehicle").Columns(columns)
        with tempfile.TemporaryDirectory() as tempdirname:
            db = Db(f"{tempdirname}/test.db", True)
            db.create_table(table)
            print(os.listdir(tempdirname))
