"""HarborMaster class."""
# pylint: disable=invalid-name,line-too-long,expression-not-assigned
from .sheets_helper import SheetsHelper

GLOBAL_TABLES = {"readme", "todo", "ref", "cyc"}

class HarborMaster:
    """HarborMaster class."""
    def __init__(self, gc, db):
        self.gc = gc
        self.db = db
        self.sheetsHelper = SheetsHelper(gc)
        self.populate_harbor_db()

    def read(self, sheet, wsheet):
        """Return rows as a list of dicts, with first row being the keys"""
        sheet = f"s.{sheet}" if not sheet.startswith("s.") else sheet
        return self.sheetsHelper.read(sheet, wsheet)

    def worksheets(self, sheet):
        """Return a list of the worksheet names in this sheet."""
        sheet = f"s.{sheet}" if not sheet.startswith("s.") else sheet
        return self.sheetsHelper.worksheets(sheet)

    def registered_ships(self):
        """Return a dictionary of registered 'ships' (sheets) in the harbor 
        along with their 'cargo' (worksheets)."""
        return {f"s.{ship['ship']}": self.sheetsHelper.worksheets(f"s.{ship['ship']}")
                for ship in self.sheetsHelper.read('s.core', 'ship-register')}

    def create_and_populate_local_table(self, ship, wsheet):
        """Populate in harbor db a worksheet specific to a single ship."""
        ship = f"s.{ship}" if not ship.startswith("s.") else ship
        rows = self.read(ship, wsheet)
        table = f"[{wsheet}]"
        self.db.run(f"DROP TABLE IF EXISTS {table}")

        if len(rows) == 0:
            return
        keys = list(rows[0].keys())
        fields = [f"{key} TEXT" for key in keys]
        self.db.run(f"CREATE TABLE {table} ({','.join(fields)})")

        values = []
        for row in rows:
            # values.append(str(tuple(row[key] for key in keys)))
            quoted = tuple(f'"{row[key]}"' for key in keys)
            values.append(f"({','.join(quoted)})")
        self.db.run(f"INSERT INTO {table} VALUES {','.join(values)}")

    def create_and_populate_global_table(self, name):
        """Populate in harbor db worksheets shared by multiple ships"""
        ships = [ship for ship, wsheets in self.registered_ships().items() if name in wsheets]
        if len(ships) == 0:
            print(f"No ships in harbor with wsheet named {name}.")
            return

        def flatten(l):
            """https://stackoverflow.com/questions/952914/how-do-i-make-a-flat-list-out-of-a-list-of-lists"""
            return [item for sublist in l for item in sublist]

        rows = flatten([[row | {"ship": ship} for row in self.read(ship, name)] for ship in ships])
        if len(rows) == 0:
            print(f"No items found in all ships under wsheet named {name}.")
            return

        table = f"[{name}]"
        self.db.run(f"DROP TABLE IF EXISTS {table}")

        keys = list(rows[0].keys())
        fields = [f"{key} TEXT" for key in keys]
        self.db.run(f"CREATE TABLE {table} ({','.join(fields)})")

        values = []
        for row in rows:
            values.append(str(tuple(row[key] for key in keys)))
        self.db.run(f"INSERT INTO {table} VALUES {','.join(values)}")

    def populate_harbor_db(self):
        """Populate all global and local tables for ships in harbor."""
        [self.create_and_populate_global_table(t) for t in GLOBAL_TABLES]
        for ship, wsheets in self.registered_ships().items():
            for wsheet in wsheets:
                if wsheet not in GLOBAL_TABLES:
                    self.create_and_populate_local_table(ship, wsheet)
