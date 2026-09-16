import pytest

from src.base import SRU, SRUError, parse_response
from tests.conftest import sru_response

ALBERTI = "ark:/12148/cb12083793k"
AERTSSENS = "ark:/12148/cb12230181h"


class FakeResponse:
    def __init__(self, content):
        self.content = content

    def raise_for_status(self):
        pass


class FakeSession:
    """Answers with the fixtures whose ARK appears in the query."""

    def __init__(self, fixtures):
        self.fixtures = fixtures
        self.queries = []

    def get(self, url, timeout, params):
        self.queries.append(params)
        names = [name for ark, name in self.fixtures.items() if ark in params["query"]]
        return FakeResponse(sru_response(*names))


@pytest.fixture
def sru():
    def make(fixtures):
        client = SRU(session=FakeSession(fixtures))
        client.DELAY = 0
        return client
    return make


def test_fetch_in_batches(sru):
    client = sru({ALBERTI: "aut_cb12083793k", AERTSSENS: "aut_cb12230181h"})
    client.BATCH_SIZE = 1
    records = client.fetch([ALBERTI, AERTSSENS, ALBERTI], "PERS")

    assert set(records) == {ALBERTI, AERTSSENS}
    assert len(client.session.queries) == 2  # duplicates asked once
    assert 'aut.status any "validated sparse"' in client.session.queries[0]["query"]


def test_fetch_one_request_for_several_arks(sru):
    client = sru({ALBERTI: "aut_cb12083793k", AERTSSENS: "aut_cb12230181h"})
    records = client.fetch([ALBERTI, AERTSSENS], "PERS")

    assert set(records) == {ALBERTI, AERTSSENS}
    assert len(client.session.queries) == 1
    assert client.session.queries[0]["query"].startswith(f'aut.persistentid any "{ALBERTI} {AERTSSENS}"')


def test_fetch_merged_record_returned_under_another_ark(sru):
    old_ark = "ark:/12148/cb00000000x"
    client = sru({old_ark: "bib_cb31721367g"})
    records = client.fetch([old_ark, "ark:/12148/cb11111111z"], "BOOK")

    assert list(records) == [old_ark]
    assert records[old_ark].get("id") == "ark:/12148/cb31721367g"


def test_fetch_batch_with_an_unreadable_record(sru):
    broken = "ark:/12148/cb12171068x"
    client = sru({ALBERTI: "aut_cb12083793k", AERTSSENS: "aut_cb12230181h"})
    get = client.session.get

    def get_or_fail(url, timeout, params):
        if broken in params["query"]:
            return FakeResponse(DIAGNOSTIC)
        return get(url, timeout, params)

    client.session.get = get_or_fail
    records = client.fetch([ALBERTI, broken, AERTSSENS], "PERS")

    assert set(records) == {ALBERTI, AERTSSENS}
    assert client.errors == {broken: "probleme lecture trame XML"}


DIAGNOSTIC = b"""<srw:searchRetrieveResponse xmlns:srw="http://www.loc.gov/zing/srw/">
  <srw:diagnostics><sd:diagnostic xmlns:sd="http://www.loc.gov/zing/srw/diagnostic/">
    <sd:message>probleme lecture trame XML</sd:message>
  </sd:diagnostic></srw:diagnostics></srw:searchRetrieveResponse>"""


def test_parse_response_diagnostic():
    with pytest.raises(SRUError, match="probleme lecture trame XML"):
        parse_response(DIAGNOSTIC)
