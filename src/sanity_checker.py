"""Sanity checks for system."""
# pylint: disable=invalid-name,too-few-public-methods,too-many-locals
import re
PEGWORD, PEGSITE, PEGDATE = "Pegword", "Pegsite", "Pegdate"
class SanityChecker:
    """Sanity checker for system"""
    def __init__(self, db):
        self.db = db
        self.passing = []
        self.failing = []

    def check(self):
        """Perform all sanity checks and print result."""
        self.__check_pegpalace()
        print(f"Sanity checks complete: {len(self.passing)} passed, {len(self.failing)} failed.")
        self.passing, self.failing = [], []

    def __check(self, condition, check_name, fail_msg):
        if condition:
            self.passing.append(check_name)
        else:
            self.failing.append(check_name)
            print(f"FAIL: {check_name}: {fail_msg}")
        return condition

    def __check_pegpalace(self):
        pegwords = self.db.all(PEGWORD)
        pegsites = self.db.all(PEGSITE)
        pegdates = self.db.all(PEGDATE)

        wordpegs = {p['peg'] for p in pegwords}
        sitepegs = {p['peg'] for p in pegsites}
        datepegs = {p['peg'] for p in pegdates}

        test = "pegword-pegsite-pegs-match"
        fail = f"Pegs do not match between {PEGWORD}, {PEGSITE}, and {PEGDATE}."
        cond = wordpegs == sitepegs and datepegs.intersection(wordpegs) == datepegs
        self.__check(cond, test, fail)

        test = "pegs-count"
        fail = "Did not find exactly 1092 pegwords/pegsites and 366 pegdates."
        cond = len(wordpegs) == 1092 and len(sitepegs) == 1092 and len(datepegs) == 366
        self.__check(cond, test, fail)

        valid_name=re.compile(r"^[a-z0-9\-]+$")
        invalid_words = {p for p in pegwords if not valid_name.match(p['word'])}
        invalid_sites = {p for p in pegsites if not (valid_name.match(p['region'])
                                                     and valid_name.match(p['site']))}
        invalid_dates = {p for p in pegdates if not (valid_name.match(p['color'])
                                                     and valid_name.match(p['celebrity']))}

        test = "pegpalace-regex"
        fail = f"Failed regex in {invalid_words} {invalid_sites} {invalid_dates}"
        cond = len(invalid_words) + len(invalid_sites) + len(invalid_dates) == 0
        self.__check(cond, test, fail)
