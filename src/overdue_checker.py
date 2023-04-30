"""Overdue checks for system."""
# pylint: disable=invalid-name,too-few-public-methods,too-many-locals
import datetime
import pytz

CYCLIC, LOGS = "Cyclic", "Logs"

class OverdueChecker:
    """Overdue checker for system"""
    def __init__(self, db):
        self.db = db

    @staticmethod
    def today():
        """Return today in PST."""
        return datetime.datetime.now(pytz.timezone('US/Pacific')).date()

    def check(self):
        """Perform all overdue checks and print result."""
        query = (
            f"SELECT "
            f"  [cyc].item, "
            f"  max_date, "
            f"  CAST(julianday('{self.today()}') - julianday(max_date) AS INTEGER) AS stale, "
            f"  CAST([cyc].days AS INTEGER) AS days "
            f"FROM [cyc] "
            f"  LEFT JOIN (SELECT item, MAX(date) AS max_date "
            f"             FROM Logs GROUP BY 1) AS MaxLogs "
            f"  ON [cyc].code = MaxLogs.code"
        )
        current_state = self.db.run(query)
        overdue = []
        for item in current_state:
            code = item['item']
            stale_days = item['stale'] if item['stale'] is not None else 1000
            amount_overdue = stale_days / item['days']
            if amount_overdue >= 1:
                overdue.append((amount_overdue, code, item['days'], item['max_date']))
        overdue.sort(reverse=True)
        for item in overdue:
            print(f"{item[1].rjust(30)} ({item[2]}d) is overdue "
                  f"by a factor of {item[0]:8.2f} ({item[3]})")
