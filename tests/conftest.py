from pathlib import Path

import pytest
from lxml import etree

from src.base import NS, parse_response

FIXTURES = Path(__file__).parent / "fixtures"


def load_record(name):
    """Record element of a real SRU response saved in tests/fixtures (e.g. "aut_cb12230181h")."""
    return next(iter(parse_response((FIXTURES / f"{name}.xml").read_bytes()).values()))


def sru_response(*names):
    """SRU response (bytes) containing the records of several fixtures."""
    root = etree.fromstring(
        b'<srw:searchRetrieveResponse xmlns:srw="http://www.loc.gov/zing/srw/"><srw:records/></srw:searchRetrieveResponse>')
    records = root.find("s:records", namespaces=NS)
    for name in names:
        records.append(load_record(name))
    return etree.tostring(root)


@pytest.fixture
def record():
    return load_record
