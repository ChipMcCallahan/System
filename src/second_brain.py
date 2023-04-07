"""Second Brain."""
# pylint: disable=invalid-name,redefined-builtin
from versatuple import versatuple

Peglist = versatuple("Peglist", ("id", "peg", "word"))
Palace = versatuple("Palace", ("region", "id", "peg", "room"))

class SecondBrain:
    """Second Brain"""
    def __init__(self, db):
        self.db = db
        self.table = None

    def convert(self, row):
        "Base convert method."
        raise ValueError("Abstract method on base class.")

    def select_all(self):
        """SELECT * FROM self.table"""
        return tuple(self.convert(r) for r in self.db.select_all(self.table))

    def insert(self, *rows):
        """INSERT INTO self.table VALUES (...)"""
        self.db.insert(self.table, rows)

    def replace_by_id(self, *rows):
        """Assumes every row has unique 'id' field. Replaces existing with new."""
        self.delete_ids(*[r.id for r in rows])
        self.insert(*rows)

    def delete_ids(self, *ids):
        """Assumes every row has unique 'id' field. Delete rows with provided ids."""
        for id in ids:
            assert isinstance(id, int)
        query = f"DELETE FROM {self.table} WHERE id IN ({', '.join([str(id) for id in ids])})"
        self.db.execute(query)

    def next_id(self):
        """Fetch the next available id."""
        query = f"SELECT MAX(id)+1 AS next_id FROM {self.table}"
        return self.db.execute(query)[0]['next_id']

    def get_where(self, condition_str):
        """WARNING: Not SQL Injection safe!"""
        query = f"SELECT * FROM {self.table} WHERE {condition_str}"
        return tuple(self.convert(r) for r in self.db.execute(query))

    def add_quote_if_str(self, maybe_str):
        """Return arg with quotes if it is a string."""
        return f"'{maybe_str}'" if isinstance(maybe_str, str) else maybe_str

class PeglistTable(SecondBrain):
    """Peglist Table"""
    def __init__(self, db):
        super().__init__(db)
        self.table = "Peglist"

    def convert(self, row):
        """Convert a row to a Peglist object."""
        return Peglist(row["id"], row["peg"], row["word"])

    def set(self, peg, word):
        """Set {peg} to {word}"""
        assert isinstance(peg, str)
        existing = self.get(peg)
        if len(existing) > 1:
            raise ValueError(f"Found duplicate pegs {peg} in db.")
        id = existing[0].id if len(existing) == 1 else self.next_id()
        self.replace_by_id(Peglist(id, peg, word))

    def get(self, peg_or_id=None):
        """Get word for {peg}"""
        if not peg_or_id:
            return self.select_all()
        kw = "peg" if isinstance(peg_or_id, str) else "id"
        result = self.get_where(f"{kw} = {self.add_quote_if_str(peg_or_id)}")
        if len(result) > 1:
            raise ValueError(f"Found duplicate pegs {result}")
        return result[0] if len(result) > 0 else None

class PalaceTable(SecondBrain):
    """Palace Table"""
    def __init__(self, db):
        super().__init__(db)
        self.table = "Palace"

    def convert(self, row):
        """Convert a row to a Palace object."""
        return Palace(row["region"], row["id"], row["peg"], row["room"])
