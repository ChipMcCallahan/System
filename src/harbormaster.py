"""HarborMaster class."""
# pylint: disable=invalid-name
from .sheets_helper import SheetsHelper

class HarborMaster:
    """HarborMaster class."""
    def __init__(self, creds):
        self.gc = creds
        self.sheetsHelper = SheetsHelper(creds)

    def read(self, sheet, wsheet):
        """Return rows as a list of dicts, with first row being the keys"""
        sheet = f"s.{sheet}" if not sheet.startswith("s.") else sheet
        return self.sheetsHelper.read(sheet, wsheet)

    def worksheets(self, sheet):
        """Return a list of the worksheet names in this sheet."""
        return self.sheetsHelper.worksheets(sheet)

    def registered_ships(self):
        """Return a dictionary of registered 'ships' (sheets) in the harbor 
        along with their 'cargo' (worksheets)."""
        return {f"s.{ship['ship']}": self.sheetsHelper.worksheets(f"s.{ship['ship']}")
                for ship in self.sheetsHelper.read('s.core', 'ship-register')}
