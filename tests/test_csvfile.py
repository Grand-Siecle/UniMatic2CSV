import codecs

from src.csvfile import read_csv, write_csv


def test_semicolon_bom_crlf_roundtrip(tmp_path):
    path = tmp_path / "fiche.csv"
    path.write_bytes(codecs.BOM_UTF8 + "BDD;ARK;ISNI;Nom;\r\nPERS1;ark:/12148/cb1;0000000118738159;Périer;\r\nPERS2;;nan;\"A ; B\";\r\n".encode())

    df, fmt = read_csv(path)
    assert (fmt.sep, fmt.encoding, fmt.lineterminator) == (";", "utf-8-sig", "\r\n")
    assert list(df.columns) == ["BDD", "ARK", "ISNI", "Nom"]  # trailing separator dropped
    assert df.at[0, "ISNI"] == "0000000118738159"  # read as text
    assert df.loc[1, ["ARK", "ISNI"]].isna().all()  # empty and "nan" cells

    write_csv(df, path, fmt)
    assert path.read_bytes() == codecs.BOM_UTF8 + "BDD;ARK;ISNI;Nom\r\nPERS1;ark:/12148/cb1;0000000118738159;Périer\r\nPERS2;;;\"A ; B\"\r\n".encode()


def test_tab_file(tmp_path):
    path = tmp_path / "fiche.csv"
    path.write_text("BDD\tARK\tNotes\nLIV1\tark:/12148/cb1\tun ; deux\n", encoding="utf-8")

    df, fmt = read_csv(path)
    assert (fmt.sep, fmt.encoding, fmt.lineterminator) == ("\t", "utf-8", "\n")
    assert df.at[0, "Notes"] == "un ; deux"
