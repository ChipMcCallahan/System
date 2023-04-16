"""Overdue checks for system."""
# pylint: disable=invalid-name,too-few-public-methods,too-many-locals
CYCLIC, LOGS = "Cyclic", "Logs"
class OverdueChecker:
    """Overdue checker for system"""
    def __init__(self, db):
        self.db = db

    def check(self):
        """Perform all overdue checks and print result."""
        query = (
            "SELECT "
            "  Cyclic.code, "
            "  max_date, "
            "  CAST(julianday('now') - julianday(max_date) AS INTEGER) AS stale, "
            "  Cyclic.days "
            "FROM Cyclic "
            "  LEFT JOIN (SELECT code, MAX(date) AS max_date "
            "             FROM Logs GROUP BY 1) AS MaxLogs "
            "  ON Cyclic.code = MaxLogs.code"
        )
        current_state = self.db.run(query)
        overdue = []
        for item in current_state:
            code = item['code']
            stale_days = item['stale'] if item['stale'] is not None else 1000
            amount_overdue = stale_days / item['days']
            if amount_overdue >= 1:
                overdue.append((amount_overdue, code, item['days'], item['max_date']))
        overdue.sort(reverse=True)
        for item in overdue:
            print(f"{item[1].rjust(30)} ({item[2]}d) is overdue "
                  f"by a factor of {item[0]:8.2f} ({item[3]})")
