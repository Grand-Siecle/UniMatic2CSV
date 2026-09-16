# -----------------------------------------------------------
# Code inspired by: Kelly Christensen
# Repository: https://github.com/kat-kel/alto2tei.git
# Python class to parse and store data from the BNF's general catalogue.
# -----------------------------------------------------------

import time

import requests
from lxml import etree
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

NS = {
    "s": "http://www.loc.gov/zing/srw/",
    "sd": "http://www.loc.gov/zing/srw/diagnostic/",
    "m": "info:lc/xmlns/marcxchange-v2",
}

USER_AGENT = "UniMatic2CSV (+https://github.com/Grand-Siecle/UniMatic2CSV)"


class SRUError(Exception):
    """The BnF SRU API answered with a diagnostic instead of records."""


def http_session():
    """requests session with a User-Agent and retries (with backoff) on temporary server errors."""
    session = requests.Session()
    retry = Retry(total=3, backoff_factor=2, status_forcelist=(429, 500, 502, 503, 504), allowed_methods=("GET",))
    session.mount("https://", HTTPAdapter(max_retries=retry))
    session.headers["User-Agent"] = USER_AGENT
    return session


def parse_response(content):
    """Parse an SRU response and return {ark: record} (raises SRUError on an API diagnostic)."""
    root = etree.fromstring(content)
    diagnostic = root.find(".//sd:diagnostic", namespaces=NS)
    if diagnostic is not None:
        details = diagnostic.findtext("sd:details", namespaces=NS)
        message = diagnostic.findtext("sd:message", namespaces=NS)
        raise SRUError(f"{message} ({details})" if details else message)
    return {record.get("id"): record for record in root.iterfind(".//m:record", namespaces=NS)}


class SRU(object):
    """Client of the BnF general catalogue SRU API: https://api.bnf.fr/fr/api-sru-catalogue-general"""

    URL = "https://catalogue.bnf.fr/api/SRU"
    BATCH_SIZE = 50  # ARKs per request (the API accepts up to 1000 records per response)
    DELAY = 1.0  # seconds between two requests, to stay polite with the BnF servers

    def __init__(self, session=None):
        self.session = session or http_session()
        self.errors = {}
        self._last_request = 0.0

    def request(self, query, maximum_records):
        wait = self.DELAY - (time.monotonic() - self._last_request)
        if wait > 0:
            time.sleep(wait)
        self._last_request = time.monotonic()
        r = self.session.get(self.URL, timeout=60, params={
            "version": "1.2",
            "operation": "searchRetrieve",
            "recordSchema": "unimarcXchange",
            "maximumRecords": maximum_records,
            "query": query,
        })
        r.raise_for_status()
        return parse_response(r.content)

    def fetch(self, arks, mode, advance=None):
        """Fetch the records of several ARKs.

        mode: 'PERS' (authority records) or 'BOOK' (bibliographic records)
        advance: optional callback, called with the number of ARKs processed (progress bar)
        Returns:
            records (dict): {ark: record XML element} for the ARKs found in the catalogue
            (self.errors keeps {ark: message} for the records the API could not send)
        """
        if mode == "PERS":
            # "sparse" authority records are only returned when explicitly asked for
            template = 'aut.persistentid {relation} "{arks}" and aut.status any "validated sparse"'
        elif mode == "BOOK":
            template = 'bib.persistentid {relation} "{arks}"'
        else:
            raise ValueError("Verify mode value error")

        arks = list(dict.fromkeys(arks))
        self.errors = {}
        records = {}
        for start in range(0, len(arks), self.BATCH_SIZE):
            batch = arks[start:start + self.BATCH_SIZE]
            found = self._fetch_batch(template, batch)
            records.update({ark: found[ark] for ark in batch if ark in found})
            if advance:
                advance(len(batch))

        # A merged record is returned under its new ARK: ask again for it alone.
        for ark in [ark for ark in arks if ark not in records and ark not in self.errors]:
            try:
                found = self.request(template.format(relation="all", arks=ark), 1)
            except SRUError as err:
                self.errors[ark] = str(err)
                continue
            if found:
                records[ark] = next(iter(found.values()))
        return records

    def _fetch_batch(self, template, batch):
        """One request for the whole batch. If an unreadable record makes it fail, split the batch in two."""
        try:
            return self.request(template.format(relation="any", arks=" ".join(batch)), len(batch))
        except SRUError as err:
            if len(batch) == 1:
                self.errors[batch[0]] = str(err)
                return {}
            middle = len(batch) // 2
            return {**self._fetch_batch(template, batch[:middle]), **self._fetch_batch(template, batch[middle:])}


class Notice(object):
    """Helpers to read a UNIMARC record (marcxchange XML element)."""

    def __init__(self, record):
        self.record = record

    def values(self, tag, code):
        """All non-empty values of a subfield, in the order of the record."""
        path = f'm:datafield[@tag="{tag}"]/m:subfield[@code="{code}"]'
        texts = (subfield.text.strip() for subfield in self.record.iterfind(path, namespaces=NS) if subfield.text)
        return [text for text in texts if text]

    def value(self, tag, code):
        """First non-empty value of a subfield, or None."""
        values = self.values(tag, code)
        return values[0] if values else None
