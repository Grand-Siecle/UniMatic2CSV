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

        ids_isni = self.root.findall('.//m:datafield[@tag="700"]', namespaces=self.NS)

        # -- identifier (700 subfield "o") --
        list_isni = []
        for id_isni in ids_isni:
            id_isni = id_isni.find('m:subfield[@code="o"]', namespaces=self.NS)
            list_isni.append(id_isni.text.strip().replace('ISNI', ''))
        if len(list_isni) > 0:
            data["ISNI"] = ' | '.join(list_isni)
        return data

    def get_title(self) -> Dict:
        fields = ["Titre_long", "Format"]

        data = {}
        {data.setdefault(f, np.NAN) for f in fields}

        id_element = self.root.find('.//m:datafield[@tag="200"]', namespaces=self.NS)

        # -- identifier (700 subfield "o") --
        has_title = id_element.find('m:subfield[@code="a"]', namespaces=self.NS)

        id_element = self.root.find('.//m:datafield[@tag="215"]', namespaces=self.NS)
        has_format = id_element.find('m:subfield[@code="d"]', namespaces=self.NS)
        if has_title is not None:
            data["Titre_long"] = has_title.text.strip()
        if has_format is not None:
            data["Format"] = has_format.text.strip()
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
            data["ID_Lieu_publication"] = has_place
        if has_place is not None:
            data["Lieu_publication"] = has_placeId
        if has_date is not None:
            has_date = datetime.strptime(has_date, "%Y%m%d").strftime("%Y/%m/%d")
            data["Date_01"] = has_date
        return data

    def get_matiere(self) -> Dict:
        fields = ["Sujet", "Cote"]

        data = {}
        {data.setdefault(f, np.NAN) for f in fields}

        ids_element = self.root.findall('.//m:datafield[@tag="606"]', namespaces=self.NS)

        # -- identifier (606 subfield "o") --
        list_rameau = []
        for id_element in ids_element:
            for letter in ['a', 'x', 'y', 'z']:
                try:
                    label_rameau = id_element.find(f'm:subfield[@code="{letter}"]', namespaces=self.NS)
                    list_rameau.append(label_rameau.text.strip())
                except AttributeError:
                    pass #Nonetype
        if len(list_rameau) > 0:
            data["Sujet"] = ' | '.join(list_rameau)

        # Cote
        id_element = self.root.find('.//m:datafield[@tag="930"]', namespaces=self.NS) # get only first ref
        has_cote = id_element.find('m:subfield[@code="a"]', namespaces=self.NS)
        if has_cote is not None:
            data["Cote"] = has_cote.text.strip()
        return data
