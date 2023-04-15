"""Tests for System."""
# pylint: disable=invalid-name

import unittest
import tempfile
from datetime import date
from src.sql_utils import Db
from src.system import System

class TestSystem(unittest.TestCase):
    """Tests for System"""

    def test_workout(self):
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
