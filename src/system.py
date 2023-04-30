"""System class"""
# pylint: disable=invalid-name,too-few-public-methods

from dateutil.parser import parse
from .harbormaster import HarborMaster
from .overdue_checker import OverdueChecker

WORKOUT = "Workout"
LOGS = "Logs"

class System:
    """System class"""
    def __init__(self, db, gc):
        self.db = db
        self.harborMaster = HarborMaster(gc, db)
        self.overdueChecker = OverdueChecker(db)

    def overdue_check(self):
        """Perform all overdue checks and print result."""
        return self.overdueChecker.check()

    def today(self):
        """Return today in PST."""
        return self.overdueChecker.today()

    def log(self, code, description="", *, date=None, new_code=False, multiple=False):
        """Log something. Specify new_code=True to allow this to be a code
        not currently in the table. Specify multiple=True to allow multiple
        writes for this (date, code) combo. Specify date and description as needed."""
        date = str(parse(date).date() if date else self.today())
        if not multiple:
            existing = self.db.run(f"SELECT * FROM {LOGS} "
                                   f"WHERE date = '{date}' AND code = '{code}';")
            if existing:
                raise ValueError(f"Log entry exists for {date} and {code}: {existing}. "
                                 f"Set multiple=True to bypass.")
        if not new_code:
            existing = self.db.run(f"SELECT * FROM {LOGS} "
                                   f"WHERE code = '{code}';")
            if not existing:
                raise ValueError(f"Code {code} is new to this table. Set new_code=True to allow.")
        next_id = self.db.run(f"SELECT COALESCE(MAX(id)+1, 0) AS next_id FROM {LOGS}")[0]['next_id']
        self.db.run(f"INSERT INTO {LOGS} VALUES ('{next_id}', '{date}', '{code}', "
                                               f"'{str(description)}')")

    def log_ride(self, miles, *, date=None, overwrite=False):
        """Log a bike ride. Default is today, pass date= to change. Adds to existing 
           unless overwrite is True. """
        date = str(parse(date).date() if date else self.today())
        ex = 'ride'
        amt = miles
        existing = self.db.run(f"SELECT * FROM {WORKOUT} "
                               f"WHERE exercise = '{ex}' AND date = '{date}'")
        if existing and not overwrite:
            amt += float(existing[0]['amount'])
        self.db.run(f"DELETE FROM {WORKOUT} WHERE exercise = '{ex}' and date = '{date}'")
        self.db.run(f"INSERT INTO {WORKOUT} VALUES ('{date}', '{ex}', '{amt}')")
