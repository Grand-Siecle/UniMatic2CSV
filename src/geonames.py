import re

import requests

from src.base import http_session
from src.console import console


class GeoNames(object):
    """Find the GeoNames id of a place name: https://www.geonames.org/export/geonames-search.html

    Each place is asked only once (cache). Without username, or when the account is refused or out of
    credits (10,000 per day, 1,000 per hour for a free account), ids are simply left empty.
    """

    URL = "https://secure.geonames.org/searchJSON"
    STOP_CODES = {10, 18, 19, 20}  # authorization error, daily / hourly / weekly limit exceeded
    # BnF qualifies foreign places by their country ("Gênes (Italie)") and French ones by their département
    COUNTRIES = {
        "allemagne": "DE", "angleterre": "GB", "autriche": "AT", "belgique": "BE", "espagne": "ES", "france": "FR",
        "grande-bretagne": "GB", "italie": "IT", "pays-bas": "NL", "pologne": "PL", "portugal": "PT",
        "royaume-uni": "GB", "suisse": "CH", "tchéquie": "CZ", "république tchèque": "CZ",
    }

    def __init__(self, username, session=None):
        self.username = username
        self.session = session or http_session()
        self.cache = {}
        self.enabled = bool(username)

    def get_id(self, place):
        if not self.enabled or not isinstance(place, str):
            return None
        name, country = self.clean(place), self.country(place)
        if not name:
            return None
        if (name, country) not in self.cache:
            self.cache[(name, country)] = self.search(name, country)
        return self.cache[(name, country)]

    @staticmethod
    def clean(place):
        """Keep the place name only: "Gênes (Italie)" -> "Gênes", "[Paris]" -> "Paris", "[S.l.]" -> ""."""
        name = re.split(r"[(,]", place.replace("[", "").replace("]", ""))[0].strip()
        return "" if re.fullmatch(r"s\.\s?l\.?", name, flags=re.IGNORECASE) else name

    @classmethod
    def country(cls, place):
        """Country code from the qualifier: "Gênes (Italie)" -> "IT", "Blois (Loir-et-Cher)" -> "FR", "Paris" -> None."""
        qualifiers = re.findall(r"\(([^)]*)\)", place) + place.split(",")[1:]
        if not qualifiers:
            return None
        return cls.COUNTRIES.get(qualifiers[-1].strip().lower(), "FR")

    def search(self, name, country=None):
        params = {"q": name, "featureClass": "P", "maxRows": 1, "lang": "fr", "isNameRequired": "true",
                  "username": self.username}
        if country:
            params["country"] = country
        else:
            params["countryBias"] = "FR"
        try:
            data = self.session.get(self.URL, params=params, timeout=30).json()
        except (requests.RequestException, ValueError) as err:
            console.print(f"GeoNames : pas de réponse pour « {name} » ({err})", style="yellow", markup=False)
            return None

        status = data.get("status")
        if status:
            console.print(f"GeoNames : {status.get('message')}", style="yellow", markup=False)
            if status.get("value") in self.STOP_CODES:
                self.enabled = False
            return None

        results = data.get("geonames") or []
        return str(results[0]["geonameId"]) if results else None
