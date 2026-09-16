import codecs

import pandas as pd
from click.testing import CliRunner

import run as cli
from src.csvfile import read_csv
from tests.conftest import load_record

HEADER = "BDD;ARK;ISNI;Prenoms;Nom;Annee_naissance;ID_Ville_naissance;Ville_naissance;Annee_mort;ID_Ville_mort;Ville_mort;Professions"
ROWS = [
    # empty cells to fill, ISNI damaged by a spreadsheet
    "PERS1;ark:/12148/cb12083793k;120958329;Leon Battista;Alberti;nan;;;;;;",
    # value already typed by hand: kept
    "PERS2;ark:/12148/cb12230181h;;Hendrick;Aertssens;;;;;;;Imprimeur à Anvers",
    # ARK of someone else: skipped
    "PERS3;ark:/12148/cb12259347g;;Jean;Dupont;;;;;;;",
    "PERS4;;;Adrien;Périer;;;;;;;",
    "PERS5;ark:/12148/cb99999999x;;Moïse;Amyraut;;;;;;;",
]
FIXTURES = {"ark:/12148/cb12083793k": "aut_cb12083793k", "ark:/12148/cb12230181h": "aut_cb12230181h",
            "ark:/12148/cb12259347g": "aut_cb12259347g"}


class FakeSRU:
    errors = {}

    def fetch(self, arks, mode, advance=None):
        return {ark: load_record(FIXTURES[ark]) for ark in arks if ark in FIXTURES}


class FakeGeoNames:
    IDS = {"Gênes (Italie)": "3176219", "Rome (Italie)": "3169070"}
    enabled = True

    def __init__(self, username):
        pass

    def get_id(self, place):
        return self.IDS.get(place)


def run_cli(tmp_path, monkeypatch, *args):
    monkeypatch.setattr(cli, "SRU", FakeSRU)
    monkeypatch.setattr(cli, "GeoNames", FakeGeoNames)
    path = tmp_path / "fiche_personne.csv"
    path.write_bytes(codecs.BOM_UTF8 + "\r\n".join([HEADER] + ROWS + [""]).encode())
    result = CliRunner().invoke(cli.run, [str(path), "pers", *args])
    assert result.exit_code == 0, result.output
    return path, result


def test_run_fills_empty_cells_only(tmp_path, monkeypatch):
    path, result = run_cli(tmp_path, monkeypatch)
    df, fmt = read_csv(path)
    alberti, aertssens, dupont, perier, amyraut = (df.loc[i] for i in range(5))

    assert alberti["ISNI"] == "0000000120958329"
    assert alberti["Annee_naissance"] == "1404/02/18"
    assert alberti["Ville_naissance"] == "Gênes (Italie)"
    assert alberti["ID_Ville_naissance"] == "3176219"
    assert alberti["ID_Ville_mort"] == "3169070"

    assert aertssens["Professions"] == "Imprimeur à Anvers"
    assert aertssens["Annee_mort"] == "1658/03/12"

    assert dupont.drop(["BDD", "ARK", "Prenoms", "Nom"]).isna().all()

    report, _ = read_csv(tmp_path / "fiche_personne_a_verifier.csv")
    problems = dict(zip(report["Ligne"], report["Probleme"]))
    assert problems == {"PERS3": "nom/titre différent", "PERS5": "notice introuvable"}
    assert "Cellules remplies" in result.output

    assert (tmp_path / "fiche_personne.csv.bak").exists()
    assert (fmt.sep, fmt.encoding, fmt.lineterminator) == (";", "utf-8-sig", "\r\n")
    assert b"nan" not in path.read_bytes()


def test_run_output_and_no_check(tmp_path, monkeypatch):
    output = tmp_path / "out.csv"
    path, result = run_cli(tmp_path, monkeypatch, "-o", str(output), "--no-check")

    assert not (tmp_path / "fiche_personne.csv.bak").exists()
    assert read_csv(path)[0].loc[0, ["Annee_naissance", "Ville_naissance"]].isna().all()  # input untouched
    df, _ = read_csv(output)
    assert df.at[2, "Annee_naissance"] == "1604?"  # PERS3 enriched despite the name difference


class AubignacNotice:
    CHECK_COLUMNS = ("Nom", "Prenoms")

    def labels(self):
        return ["Aubignac", "Hédelin d'Aubignac", "Hédelin"]  # 200 $a then 400 $a


def test_matches_variant_names_and_swapped_columns():
    assert cli.matches(pd.Series({"Prenoms": "François", "Nom": "Hédelin"}), AubignacNotice())
    assert cli.matches(pd.Series({"Prenoms": "Aubignac", "Nom": None}), AubignacNotice())
    assert not cli.matches(pd.Series({"Prenoms": "Thomas", "Nom": "Soubron"}), AubignacNotice())
