# -----------------------------------------------------------
# Code inspired by: Kelly Christensen
# Repository: https://github.com/kat-kel/alto2tei.git
# Python class to parse and store data from the BNF's general catalogue.
# -----------------------------------------------------------

import numpy as np
from lxml import etree
from typing import Dict
from datetime import datetime

from src.base import SRU
from src.opt.tools import get_geonames_id


class Book(SRU):
    def __init__(self, ark):
        super().__init__(ark)
        self.root, self.perfect_match = self.request(mode='BOOK')

    def id_data(self) -> Dict:
        fields = ["ISNI"]

        data = {}
        {data.setdefault(f, np.NAN) for f in fields}

        id_element = self.root.find('.//m:datafield[@tag="010"]', namespaces=self.NS)

        # -- identifier (010s subfield "a") --
        has_isni = id_element.find('m:subfield[@code="a"]', namespaces=self.NS)
        if has_isni is not None:
            data["ISNI"] = has_isni.text.strip()
        return data