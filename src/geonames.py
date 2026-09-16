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

    def __init__(self, username, session=None):
        self.username = username
        self.session = session or http_session()
        self.cache = {}
        self.enabled = bool(username)

    def get_id(self, place):
        if not self.enabled or not isinstance(place, str) or not place.strip():
            return None
        name = self.clean(place)
        if name not in self.cache:
            self.cache[name] = self.search(name)
        return self.cache[name]

    @staticmethod
    def clean(place):
        """Keep the place name only: "Gênes (Italie)" -> "Gênes", "Pont-à-Mousson, Meurthe-et-Moselle" -> "Pont-à-Mousson"."""
        return re.split(r"[(,\[]", place)[0].strip()

    def search(self, name):
        params = {"q": name, "featureClass": "P", "maxRows": 1, "lang": "fr", "username": self.username}
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
