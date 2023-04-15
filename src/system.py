"""System class"""
# pylint: disable=invalid-name,too-few-public-methods

import datetime
from dateutil.parser import parse

WORKOUT = "Workout"

class System:
    """System class"""
    def __init__(self, db):
        self.db = db

    def log_ride(self, miles, *, date=None, overwrite=False):
        """Log a bike ride. Default is today, pass date= to change. Adds to existing 
           unless overwrite is True. """
        date = str(parse(date).date() if date else datetime.date.today())
        ex = 'ride'
        amt = miles
        existing = self.db.run(f"SELECT * FROM {WORKOUT} "
                               f"WHERE exercise = '{ex}' AND date = '{date}'")
        if existing and not overwrite:
            amt += float(existing[0]['amount'])
        self.db.run(f"DELETE FROM {WORKOUT} WHERE exercise = '{ex}' and date = '{date}'")
        self.db.run(f"INSERT INTO {WORKOUT} VALUES ('{date}', '{ex}', '{amt}')")
