# -----------------------------------------------------------
# Code inspired by: Kelly Christensen
# Repository: https://github.com/kat-kel/alto2tei.git
# Python class to parse and store data from the BNF's general catalogue.
# -----------------------------------------------------------

from typing import Dict

from src.base import NS, Notice
from src.opt.tools import marc_date
from src.opt.variables import MULTI_SEP


class Person(Notice):
    """Authority record of a person (200) or of a corporate body (210)."""

    # CSV columns compared with the names of the record (first and last names are sometimes swapped)
    CHECK_COLUMNS = ("Nom", "Prenoms")
    # place column -> GeoNames id column
    PLACES = {"Ville_naissance": "ID_Ville_naissance", "Ville_mort": "ID_Ville_mort"}

    def labels(self):
        # -- name (200/210 subfield "a") and its variants (400/410 subfield "a"), e.g. "Aubignac", "Hédelin" --
        return self.values("200", "a") + self.values("210", "a") + self.values("400", "a") + self.values("410", "a")

    def is_person(self):
        """False for a work record (230/240: e.g. "Pascal. Pensées"), whose dates are not those of a person."""
        return bool(self.values("200", "a") or self.values("210", "a"))

    def id_data(self) -> Dict:
        # -- identifier (010 subfield "a") --
        return {"ISNI": self.value("010", "a")}

    def life_data(self) -> Dict:
        # -- dates (103 subfield "a"), fixed positions: "±YYYYMMDD?±YYYYMMDD?" (- = before Christ, ? = uncertain) --
        dates = (self.record.findtext('m:datafield[@tag="103"]/m:subfield[@code="a"]', namespaces=NS) or "").ljust(20)

        # -- places (301 subfield "a" = birth, "b" = death) --
        return {
            "Annee_naissance": self._date(dates[0:10]),
            "Ville_naissance": self.value("301", "a"),
            "Annee_mort": self._date(dates[10:20]),
            "Ville_mort": self.value("301", "b"),
        }

    def activity_data(self) -> Dict:
        # -- activities (300 subfield "a", one field per note) --
        notes = self.values("300", "a")
        return {"Professions": MULTI_SEP.join(notes) if notes else None}

    def to_dict(self) -> Dict:
        return {**self.id_data(), **self.life_data(), **self.activity_data()}

    @staticmethod
    def _date(coded):
        """" 15860522 " -> "1586/05/22", "-0384     " -> "-384", " 1604    ?" -> "1604?"."""
        date = marc_date(coded[1:9])
        if not date:
            return None
        year, _, rest = date.partition("/")
        if year.isdigit():
            year = str(int(year))  # "0055" -> "55"
        date = ("-" if coded[0] == "-" else "") + year + ("/" + rest if rest else "")
        return date + "?" if coded[9] == "?" else date
