"""SheetsHelper class, for use in Colab notebooks."""
# pylint: disable=invalid-name,too-few-public-methods,protected-access,import-error,dangerous-default-value

# from google.colab import auth
# from google.auth import default
# auth.authenticate_user()
# creds, _ = default()
# gc = gspread.authorize(creds)
# sheets_helper = SheetsHelper(gc)

DEFAULT_WSHEETS = {'readme': 1, 'todo': 1, 'ref': 2, 'cyc': 2}
COL_WIDTH = 500
DEFAULT_N_ROWS = 100
class SheetsHelper:
    """SheetsHelper class, for use in Colab notebooks."""
    def __init__(self, creds):
        self.gc = creds

    @staticmethod
    def _resize_all_columns(sheet, wsheet, size):
        sheet.batch_update(
        {
            "requests": [
                {
                    "updateDimensionProperties": {
                        "range": {
                            "sheetId": wsheet._properties['sheetId'],
                            "dimension": "COLUMNS",
                            "startIndex": 0,
                            "endIndex": wsheet._properties['gridProperties']['columnCount']
                        },
                        "properties": {
                            "pixelSize": size
                        },
                        "fields": "pixelSize"
                    }
                }
            ]
        }
    )

    def sheet(self, name, *, default_wsheets=DEFAULT_WSHEETS,
                             col_width=COL_WIDTH, default_n_rows=DEFAULT_N_ROWS):
        '''Create a new sheet with default worksheets.'''
        name = name if name.startswith("s.") else "s." + name
        sheet = self.gc.create(name)
        wsheets = []
        for wsheet_name, n_col in default_wsheets.items():
            wsheets.append(sheet.add_worksheet(title=wsheet_name, rows=default_n_rows, cols=n_col))
            for wsheet in wsheets:
                self._resize_all_columns(sheet, wsheet, col_width)
        sheet.del_worksheet(sheet.worksheet("Sheet1"))
