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

    def id_author(self) -> Dict:
        fields = ["ISNI"]

        data = {}
        {data.setdefault(f, np.NAN) for f in fields}

        id_element = self.root.find('.//m:datafield[@tag="700"]', namespaces=self.NS)

        # -- identifier (700 subfield "o") --
        has_isni = id_element.find('m:subfield[@code="o"]', namespaces=self.NS)
        if has_isni is not None:
            data["ISNI"] = has_isni.text.strip().replace('ISNI', '')
        return data

    def get_title(self) -> Dict:
        fields = ["Titre_long"]

        data = {}
        {data.setdefault(f, np.NAN) for f in fields}

        id_element = self.root.find('.//m:datafield[@tag="200"]', namespaces=self.NS)

        # -- identifier (700 subfield "o") --
        has_title = id_element.find('m:subfield[@code="a"]', namespaces=self.NS)
        if has_title is not None:
            data["Titre_long"] = has_title.text.strip()
        return data

    def get_publication(self) -> Dict:
        fields = ["ID_Lieu_publication", "Lieu_publication", "Date"]

        data = {}
        {data.setdefault(f, np.NAN) for f in fields}

        id_element = self.root.find('.//m:datafield[@tag="210"]', namespaces=self.NS)

        # -- identifier (700 subfield "o") --
        has_place = id_element.find('m:subfield[@code="a"]', namespaces=self.NS).text.strip()
        has_placeId = get_geonames_id(has_place)

        has_date = id_element.find('m:subfield[@code="d"]', namespaces=self.NS).text.strip()
        if has_place is not None:
            data["ID_Lieu_publication"] = has_place.text.strip()
        if has_place is not None:
            data["Lieu_publication"] = has_placeId.text.strip()
        if has_date is not None:
            data["Date"] = has_date.text.strip()
        return data

    def get_matiere(self) -> Dict:
        fields = ["Titre_long"]

        data = {}
        {data.setdefault(f, np.NAN) for f in fields}

        id_element = self.root.find('.//m:datafield[@tag="200"]', namespaces=self.NS)

        # -- identifier (700 subfield "o") --
        has_title = id_element.find('m:subfield[@code="a"]', namespaces=self.NS)
        if has_title is not None:
            data["Titre_long"] = has_title.text.strip()
        return data
