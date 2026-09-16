import re
import unicodedata
from difflib import SequenceMatcher

from src.opt.variables import ARK_BNF


def normalize_ark(value):
    """Extract the BnF catalogue ARK from a cell (bare ARK or catalogue URL), None otherwise."""
    if not isinstance(value, str):
        return None
    match = re.search(ARK_BNF, value)
    return match.group(0) if match else None


def normalize_isni(value):
    """Restore the 16 characters of an ISNI whose leading zeros were dropped by a spreadsheet."""
    if not isinstance(value, str):
        return value
    compact = value.replace(" ", "").upper()
    if re.fullmatch(r"\d{1,15}[\dX]", compact):
        return compact.zfill(16)
    return value


def marc_date(value):
    """Convert a UNIMARC coded date (YYYYMMDD, unknown parts blank or dotted) to YYYY/MM/DD.

    " 15860522" -> "1586/05/22", "166505  " -> "1665/05", "16..    " -> "16.."
    """
    value = (value or "").strip()
    year = value[0:4]
    if not year:
        return None
    parts = [year] + [part for part in (value[4:6], value[6:8]) if part.isdigit()]
    return "/".join(parts)


def _simplify(text):
    """Lowercase, no accents, only letters and digits separated by spaces."""
    text = unicodedata.normalize("NFKD", str(text))
    text = "".join(c for c in text if not unicodedata.combining(c)).lower()
    return " ".join(re.findall(r"[a-z0-9]+", text))


def similarity(csv_value, bnf_value):
    """Score between 0 and 1 telling how much a CSV value (name, short title) looks like the BnF one.

    Returns 1 when there is nothing to compare.
    """
    a, b = _simplify(csv_value or ""), _simplify(bnf_value or "")
    if not a or not b:
        return 1.0
    if min(len(a), len(b)) >= 3 and (a in b or b in a):
        return 1.0
    prefix = SequenceMatcher(None, a, b[:len(a)]).ratio()
    words = [w for w in a.split() if len(w) > 3]
    overlap = sum(w in b.split() for w in words) / len(words) if words else 0.0
    return max(prefix, overlap)
