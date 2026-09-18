import codecs
from dataclasses import dataclass

import pandas as pd


@dataclass
class CsvFormat:
    sep: str
    encoding: str
    lineterminator: str


def detect_format(path):
    """Guess separator (";" or tab), BOM and line endings, to write the file back the same way."""
    with open(path, "rb") as f:
        sample = f.read(64 * 1024)
    encoding = "utf-8-sig" if sample.startswith(codecs.BOM_UTF8) else "utf-8"
    sep = "\t" if sample.count(b"\t") > sample.count(b";") else ";"
    lineterminator = "\r\n" if b"\r\n" in sample else "\n"
    return CsvFormat(sep, encoding, lineterminator)


def read_csv(path, header=0):
    """Read every cell as text (keeps ISNI leading zeros); empty cells and "nan" become NaN."""
    fmt = detect_format(path)
    df = pd.read_csv(path, sep=fmt.sep, encoding=fmt.encoding, header=header, dtype=str,
                     keep_default_na=False, na_values=["", "nan", "NaN"])
    # columns created by trailing separators
    empty = [c for c in df.columns if str(c).startswith("Unnamed:") and df[c].isna().all()]
    return df.drop(columns=empty), fmt


def write_csv(df, path, fmt):
    df.to_csv(path, sep=fmt.sep, encoding=fmt.encoding, lineterminator=fmt.lineterminator, index=False)
