# REGEX

# ARK of a record in the BnF general catalogue (bibliographic or authority record): "cb" + 8 digits + check character
ARK_BNF = r"ark:/12148/cb\d{8}[0-9a-z]"

# Format of the book (UNIMARC 215 $d, e.g. "in-4", "in-fol.") -> vocabulary of the CSV files
FORMATS = {
    "fol": "in-folio",
    "plano": "in-plano",
    "4": "in-quarto",
    "8": "in-octavo",
    "12": "in-douze",
    "16": "in-seize",
    "18": "in-dix-huit",
    "24": "in-vingt-quatre",
    "32": "in-trente-deux",
}

# Separator used when a cell receives several values
MULTI_SEP = "|"
