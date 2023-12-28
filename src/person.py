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


class Person(SRU):
    def __init__(self, ark):
        super().__init__(ark)
        self.root, self.perfect_match = self.request(mode='PERS')

    def id_data(self) -> Dict:
        fields = ["ISNI"]
        
        data = {}
        {data.setdefault(f, np.NAN) for f in fields}

        id_element = self.root.find('.//m:datafield[@tag="010"]', namespaces=self.NS)

        # -- identifier (010s subfield "a") --
        if id_element is not None:
            has_isni = id_element.find('m:subfield[@code="a"]', namespaces=self.NS)
        else:
            has_isni = None
        if has_isni is not None:
            data["ISNI"] = has_isni.text.strip()
        return data

    def life_data(self) -> Dict:
        fields = ["Annee_naissance", "Ville_naissance", "ID_Ville_naissance", "Annee_mort", "Ville_mort", "ID_Ville_mort"]

        data = {}
        {data.setdefault(f, np.NAN) for f in fields}

        # -- dates (103) --
        date_element = self.root.find('.//m:datafield[@tag="103"]', namespaces=self.NS)
        if date_element is not None:
            has_dates = date_element.find('m:subfield[@code="a"]', namespaces=self.NS).text.strip().split('  ')
            try:
                has_dateBirth = datetime.strptime(has_dates[0], "%Y%m%d").strftime("%Y/%m/%d")
            except:
                has_dateBirth = has_dates[0]
            try:
                has_dateDeath = datetime.strptime(has_dates[1], "%Y%m%d").strftime("%Y/%m/%d")
            except:
                has_dateDeath = has_dates[1]
        else:
            has_dateBirth, has_dateDeath = None, None

        # -- places (301) --
        place_element = self.root.find('.//m:datafield[@tag="301"]', namespaces=self.NS)

        if place_element is not None:
            has_placeBirth = place_element.find('m:subfield[@code="a"]', namespaces=self.NS).text.strip()
            has_placeBirthId = get_geonames_id(has_placeBirth)

            has_placeDeath = place_element.find('m:subfield[@code="b"]', namespaces=self.NS).text.strip()
            has_placeDeathId = get_geonames_id(has_placeDeath)
        else:
            has_placeBirth, has_placeBirthId, has_placeDeath, has_placeDeathId = None, None, None, None

        if has_dateBirth is not None:
            data["Annee_naissance"] = has_dateBirth
        if has_placeBirth is not None:
            data["Ville_naissance"] = has_placeBirth
        if has_placeBirthId is not None:
            data["ID_Ville_naissance"] = has_placeBirthId
        if has_dateDeath is not None:
            data["Annee_mort"] = has_dateDeath
        if has_placeDeath is not None:
            data["Ville_mort"] = has_placeDeath
        if has_placeDeathId is not None:
            data["ID_Ville_mort"] = has_placeDeathId
        return data

    def activity_data(self) -> Dict:
        fields = ["Professions"]

        data = {}
        {data.setdefault(f, np.NAN) for f in fields}

        # -- activités (300) --
        activity = self.root.find('.//m:datafield[@tag="300"]', namespaces=self.NS)
        has_job = activity.find('m:subfield[@code="a"]', namespaces=self.NS).text.strip() if activity is not None else None
        if has_job is not None:
            data["Professions"] = has_job
        return data
