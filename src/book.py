# -----------------------------------------------------------
# Code inspired by: Kelly Christensen
# Repository: https://github.com/kat-kel/alto2tei.git
# Python class to parse and store data from the BNF's general catalogue.
# -----------------------------------------------------------

import re
from typing import Dict

from src.base import NS, Notice
from src.opt.variables import FORMATS, MULTI_SEP


class Book(Notice):
    """Bibliographic record."""

    # CSV columns compared with the title of the record
    CHECK_COLUMNS = ("Titre_abrege",)
    # place column -> GeoNames id column
    PLACES = {"Lieu_publication": "ID_Lieu_publication"}

    def labels(self):
        return self.values("200", "a")

    def reproduction(self):
        """True for a microform or facsimile record: its place and date are those of the reproduction."""
        coded = self.value("100", "a") or ""
        return coded[8:9] == "e" or any("microforme" in v.lower() for v in self.values("200", "b"))

    def get_title(self) -> Dict:
        # -- title (200 subfield "a") and format (215 "d", sometimes written in 215 "a" or 210 "d") --
        return {"Titre_long": self.value("200", "a"), "Format": self._format()}

    def get_publication(self) -> Dict:
        if self.reproduction():
            return {"Lieu_publication": None, "Date_01": None}
        # -- place: normalised form (620 "d") if any, else as printed (214 or 210 "a"), never "[S.l.]" --
        places = self.values("620", "d") + self.values("214", "a") + self.values("210", "a")
        place = next((p for p in places if not re.fullmatch(r"\[?\(?s\.\s?l\.?\)?\]?", p, flags=re.IGNORECASE)), None)
        return {"Lieu_publication": place, "Date_01": self._date()}

    def get_matiere(self) -> Dict:
        # -- subjects (606): one heading "a -- x -- y -- z" per field --
        headings = []
        for field in self.record.iterfind('m:datafield[@tag="606"]', namespaces=NS):
            parts = [subfield.text.strip() for subfield in field.iterfind("m:subfield", namespaces=NS)
                     if subfield.get("code") in ("a", "x", "y", "z") and subfield.text and subfield.text.strip()]
            if parts:
                headings.append(" -- ".join(parts))

        # -- shelfmark (930 "a"): digitised copies (NUMM-...) first, else the first copy --
        cotes = self.values("930", "a")
        digitised = [cote for cote in cotes if cote.startswith("NUMM-")]
        cote = MULTI_SEP.join(digitised) if digitised else (cotes[0] if cotes else None)

        return {"Sujet": MULTI_SEP.join(headings) if headings else None, "Cote": cote}

    def to_dict(self) -> Dict:
        return {**self.get_title(), **self.get_publication(), **self.get_matiere()}

    def _format(self):
        for text in self.values("215", "d") + self.values("215", "a") + self.values("210", "d"):
            match = re.search(r"\bin-?\s*(fol|plano|\d+)", text, flags=re.IGNORECASE)
            if match and match.group(1).lower() in FORMATS:
                return FORMATS[match.group(1).lower()]
        return None  # e.g. "23 cm" or "35 mm" (microfilm): not a format of the CSV vocabulary

    def _date(self):
        # coded publication date (100 "a", positions 9-12) is cleaner than the printed one (210 "d")
        coded = self.value("100", "a") or ""
        if coded[9:13].strip():
            return coded[9:13].strip()
        printed = self.value("214", "d") or self.value("210", "d")
        match = re.search(r"\d{4}", printed or "")
        return match.group(0) if match else None  # e.g. "Imprimé ceste année"
