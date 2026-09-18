import pytest

from src.opt.tools import marc_date, normalize_ark, normalize_isni, similarity


@pytest.mark.parametrize("value, expected", [
    ("ark:/12148/cb31721367g", "ark:/12148/cb31721367g"),
    (" ark:/12148/cb31721367g ", "ark:/12148/cb31721367g"),
    ("https://catalogue.bnf.fr/ark:/12148/cb31721367g.public", "ark:/12148/cb31721367g"),
    ("ark:/12148/cb335714938a", "ark:/12148/cb335714938"),  # typo after the check character
    ("https://archivesetmanuscrits.bnf.fr/ark:/12148/cc542489", None),  # not the general catalogue
    ("https://n2t.net/ark:/13960/t1sf5tp5w", None),
    ("c", None),
    (float("nan"), None),
])
def test_normalize_ark(value, expected):
    assert normalize_ark(value) == expected


@pytest.mark.parametrize("value, expected", [
    ("118738159", "0000000118738159"),
    ("000000005181040X", "000000005181040X"),
    ("51810 40x", "000000005181040X"),
    ("not an isni", "not an isni"),
    (None, None),
])
def test_normalize_isni(value, expected):
    assert normalize_isni(value) == expected


@pytest.mark.parametrize("value, expected", [
    ("15860522", "1586/05/22"),
    ("166505  ", "1665/05"),
    ("1602    ", "1602"),
    ("16..    ", "16.."),
    ("        ", None),
])
def test_marc_date(value, expected):
    assert marc_date(value) == expected


def test_similarity_same_title_with_spelling_differences():
    assert similarity("Le Portrait de Scipion l’Africain", "Le portrait de Scipion l'Africain : ou L'image de la gloire") == 1
    assert similarity("Éléments de pourtraiture, ou La méthode", "Elémens de pourtraiture ou La métode de représenter") >= 0.6
    assert similarity("Tevernier", "Tavernier") >= 0.6


def test_similarity_different_title():
    assert similarity("Traicté de l'essence et guerison de l'amour", "La sagesse mystérieuse des anciens") < 0.6


def test_similarity_nothing_to_compare():
    assert similarity("", "Andries") == 1
    assert similarity("Andries", None) == 1
