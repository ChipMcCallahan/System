"""System class"""
# pylint: disable=invalid-name,too-few-public-methods

import datetime
from collections import defaultdict
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

    def log_all(self, *codes):
        """Log all supplied codes for today."""
        for code in codes:
            self.log(code)

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

    def workout(self, workout, amount, *, date=None, overwrite=False):
        """Log a workout. Default is today, pass date= to change. Adds to existing 
           unless overwrite is True. """
        date = str(parse(date).date() if date else self.today())
        existing = self.db.run(f"SELECT * FROM {WORKOUT} "
                               f"WHERE exercise = '{workout}' AND date = '{date}'")
        if existing and not overwrite:
            amount += float(existing[0]['amount'])
        self.db.run(f"DELETE FROM {WORKOUT} WHERE exercise = '{workout}' and date = '{date}'")
        self.db.run(f"INSERT INTO {WORKOUT} VALUES ('{date}', '{workout}', '{amount}')")
        self.log(workout, date=date, new_code=True)

    def log_ride(self, miles, *, date=None, overwrite=False):
        """Log a bike ride. Default is today, pass date= to change. Adds to existing 
           unless overwrite is True. """
        self.workout("ride", miles, date=date, overwrite=overwrite)

    def log_run(self, miles, *, date=None, overwrite=False):
        """Log a run. Default is today, pass date= to change. Adds to existing 
           unless overwrite is True. """
        self.workout("run", miles, date=date, overwrite=overwrite)

    def log_pool_specs(self, cl, ph, alk=None):
        """Log pH, Cl, and (optionally) alkalinity."""
        self.log("pool-cl", cl, new_code=True)
        self.log("pool-ph", ph, new_code=True)
        if alk is not None:
            self.log("pool-alk", alk)

    def log_pool_notes(self, note):
        """Log notes for pool (e.g. chem adds)."""
        self.log("pool-notes", note)

    def get_calendar_entry(self, d):
        """Retrieve calendar info for date d."""
        d = parse(d) if isinstance(d, str) else d
        if not str(d.year) in self.harborMaster.worksheets("calendar"):
            return None
        results = self.db.run(f"SELECT * FROM [{d.year}] WHERE date = '{d.strftime('%Y-%m-%d')}'")
        return results[0] if len(results) > 0 else None

    def get_calendar_flashcards(self, start, n_days):
        """Generate {n_days} calendar flashcards from {start}"""
        start = parse(start) if isinstance(start, str) else start
        cards = []
        for i in range(n_days):
            entry = self.get_calendar_entry(start + datetime.timedelta(days=i))
            cards.append(
                f"- {entry['date']}>>{entry['color']}-{entry['weekday']}: {entry['event']}"
            )
        return cards

    def daily_flashcards(self):
        """Return a list of daily flashcards to practice in Remnote."""
        ships = [item['ship'] for item in self.db.all('[ship-register]')]
        cards = []

        berth_cards = defaultdict(list)
        for i, ship in enumerate(ships):
            berth = f"{i:03d}"
            # Cards for which ships are in which berths.
            berth_cards[berth].append(f"ship '{ship}' in berth {berth}.")

            # Cards for non-standard worksheets on ships + their schemas.
            wsheets = set(self.harborMaster.worksheets(ship)) \
                      .difference({'readme', 'todo', 'ref', 'cyc'})
            for wsheet in wsheets:
                keys = list(self.harborMaster.read(ship, wsheet)[0].keys())
                berth_cards[berth].append(f"({ship + ', ' + wsheet}) has schema {str(keys)}.")

            # Cards for standard worksheets on ships.
            for wsheet in ('readme', 'ref', 'cyc', 'todo'):
                for item in self.harborMaster.read(ship, wsheet):
                    berth_cards[berth].append(f"({ship}, {wsheet}): {str(item)}")

        for berth, items in berth_cards.items():
            for i, item in enumerate(items):
                letter_index = f"{chr(i // 26 + ord('A'))}{chr(i % 26 + ord('A'))}" # AA, AB, etc
                cards.append(f"- {berth}.{letter_index}>>{item}")

        # Cards for next 30 calendar days
        cards.extend(self.get_calendar_flashcards(self.today(), 30))

        return cards
