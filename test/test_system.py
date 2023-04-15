"""Tests for System."""
# pylint: disable=invalid-name

import unittest
import tempfile
from datetime import date
from src.sql_utils import Db
from src.system import System

class TestSystem(unittest.TestCase):
    """Tests for System"""

    def test_log(self):
        """Unit tests for the Logs table"""
        with tempfile.TemporaryDirectory() as tempdirname:
            db = Db(f"{tempdirname}/test.db", create=True)
            db.run("CREATE TABLE Logs(id INTEGER PRIMARY KEY, "
                                     "date TEXT NOT NULL, "
                                     "code TEXT NOT NULL, "
                                     "description TEXT) WITHOUT ROWID")
            sys = System(db)
            with self.assertRaises(ValueError) as err:
                sys.log("new-code")
                self.assertIn('Code new-code is new to this table', err.exception)
            sys.log("new-code", new_code=True)
            self.assertEqual(db.all("Logs"),
                                [{"id": 0,
                                  "date": str(date.today()),
                                  "code": "new-code",
                                  "description": ""}])
            with self.assertRaises(ValueError) as err:
                sys.log("new-code")
                self.assertIn('Log entry exists for', err.exception)
            sys.log("new-code", multiple=True)
            self.assertEqual(db.all("Logs"),
                                [{"id": 0,
                                  "date": str(date.today()),
                                  "code": "new-code",
                                  "description": ""},
                                  {"id": 1,
                                  "date": str(date.today()),
                                  "code": "new-code",
                                  "description": ""}])
            db.run("DELETE FROM Logs WHERE True;")
            sys.log("pool-ph", 7.5, new_code=True, date="2023-01-23")
            self.assertEqual(db.all("Logs"),
                                [{"id": 0,
                                  "date": "2023-01-23",
                                  "code": "pool-ph",
                                  "description": "7.5"}])

    def test_log_workout(self):
        """Unit tests for the Workout table."""
        with tempfile.TemporaryDirectory() as tempdirname:
            db = Db(f"{tempdirname}/test.db", create=True)
            db.run("CREATE TABLE Workout (date TEXT NOT NULL, "
                                          "exercise TEXT NOT NULL, "
                                          "amount REAL NOT NULL, "
                                          "PRIMARY KEY (date, exercise))")
            sys = System(db)
            sys.log_ride(4)
            self.assertEqual(db.all("Workout"),
                                [{"date": str(date.today()),
                                "exercise": "ride",
                                "amount": 4}])
            sys.log_ride(6.32)
            self.assertEqual(db.all("Workout"),
                                [{"date": str(date.today()),
                                "exercise": "ride",
                                "amount": 10.32}])
            sys.log_ride(7, overwrite=True)
            self.assertEqual(db.all("Workout"),
                                [{"date": str(date.today()),
                                "exercise": "ride",
                                "amount": 7}])
            sys.log_ride(6, date="1984-01-23")
            self.assertCountEqual(db.all("Workout"),
                                [{"date": str(date.today()),
                                "exercise": "ride",
                                "amount": 7},
                                {"date": "1984-01-23",
                                "exercise": "ride",
                                "amount": 6},
                                ])
