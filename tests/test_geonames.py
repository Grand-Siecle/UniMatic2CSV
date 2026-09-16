from src.geonames import GeoNames


class FakeResponse:
    def __init__(self, data):
        self.data = data

    def json(self):
        return self.data


class FakeSession:
    def __init__(self, *answers):
        self.answers = list(answers)
        self.params = []

    def get(self, url, params, timeout):
        self.params.append(params)
        return FakeResponse(self.answers.pop(0))


def test_clean_place_name():
    assert GeoNames.clean("Gênes (Italie)") == "Gênes"
    assert GeoNames.clean("Pont-à-Mousson, Meurthe-et-Moselle") == "Pont-à-Mousson"
    assert GeoNames.clean("[Paris]") == "Paris"
    assert GeoNames.clean("[S.l.]") == ""


def test_country_from_the_qualifier():
    assert GeoNames.country("Avila, Espagne") == "ES"
    assert GeoNames.country("Anchiano (près de Vinci) (Italie)") == "IT"
    assert GeoNames.country("Mâcon (Saône-et-Loire)") == "FR"  # a département
    assert GeoNames.country("Paris") is None


def test_each_place_is_asked_once():
    session = FakeSession({"geonames": [{"geonameId": 3176219}]})
    geonames = GeoNames("user", session=session)

    assert geonames.get_id("Gênes (Italie)") == "3176219"
    assert geonames.get_id("Gênes, Italie") == "3176219"
    assert len(session.params) == 1
    assert session.params[0]["q"] == "Gênes" and session.params[0]["country"] == "IT"


def test_no_country_qualifier_prefers_france():
    session = FakeSession({"geonames": [{"geonameId": 2988507}]})
    GeoNames("user", session=session).get_id("Paris")
    assert session.params[0]["countryBias"] == "FR" and "country" not in session.params[0]


def test_unknown_place_is_not_asked():
    session = FakeSession()
    assert GeoNames("user", session=session).get_id("[S.l.]") is None
    assert session.params == []


def test_stop_when_the_account_is_refused():
    session = FakeSession({"status": {"message": "user does not exist.", "value": 10}})
    geonames = GeoNames("wrong", session=session)

    assert geonames.get_id("Paris") is None
    assert geonames.get_id("Lyon") is None
    assert len(session.params) == 1


def test_without_username_no_request():
    session = FakeSession()
    assert GeoNames(None, session=session).get_id("Paris") is None
    assert session.params == []
