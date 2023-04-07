"""Tests for Second Brain."""
# pylint: disable=invalid-name

import unittest
import tempfile
from src.second_brain import Peglist, PeglistTable
from src.sql_utils import Db

class TestSecondBrain(unittest.TestCase):
    """Tests for Second Brain."""

    def test_peglist_table(self):
        """Tests for PeglistTable"""
        with tempfile.TemporaryDirectory() as tempdirname:
            db = Db(f"{tempdirname}/test.db", create=True)
            db.create_table("Peglist", (("id", "INTEGER"),
                                        ("peg", "TEXT"),
                                        ("word", "TEXT")))
            peglistTable = PeglistTable(db)

            p1 = Peglist(1, "001", "siesta")
            peglistTable.insert(p1)
            self.assertSetEqual({p1}, set(peglistTable.select_all()))

            p2 = Peglist(2, "002", "assassin")
            p3 = Peglist(3, "003", "sesame")
            peglistTable.insert(p2, p3)
            self.assertSetEqual({p1, p2, p3}, set(peglistTable.select_all()))

            results = peglistTable.get_where("peg = '002' OR word = 'sesame'")
            self.assertSetEqual(set(results), {p2, p3})

            self.assertEqual(p3, peglistTable.get("003"))
            self.assertEqual(p3, peglistTable.get(3))

            p2_ = Peglist(2, "002", "season")
            p1_ = Peglist(1, "001", "zest")
            peglistTable.replace_by_id(p1_, p2_)
            self.assertSetEqual({p1_, p2_, p3}, set(peglistTable.select_all()))

            peglistTable.delete_ids(1, 2)
            self.assertSetEqual({p3}, set(peglistTable.select_all()))

            self.assertEqual(peglistTable.next_id(), 4)
