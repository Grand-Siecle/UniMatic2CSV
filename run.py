import os
import shutil
from pathlib import Path

import click
import pandas as pd
from rich import box
from rich.panel import Panel
from rich.progress import BarColumn, MofNCompleteColumn, Progress, TextColumn, TimeElapsedColumn
from rich.table import Table
from rich.text import Text

from src.base import SRU
from src.book import Book
from src.console import console
from src.csvfile import read_csv, write_csv
from src.geonames import GeoNames
from src.opt.tools import normalize_ark, normalize_isni, similarity
from src.person import Person

NOTICES = {"PERS": Person, "BOOK": Book}
MIN_SIMILARITY = 0.6
MAX_ISSUES_SHOWN = 20


def row_label(df, index, header):
    if "BDD" in df.columns and pd.notna(df.at[index, "BDD"]):
        return df.at[index, "BDD"]
    return f"ligne {index + header + 2}"


def matches(row, notice):
    """True if the name / short title of the CSV row looks like one of those of the BnF record."""
    csv_values = [row[column] for column in notice.CHECK_COLUMNS if column in row and pd.notna(row[column])]
    scores = [similarity(value, label) for value in csv_values for label in notice.labels()]
    return not scores or max(scores) >= MIN_SIMILARITY


def bnf_copy(row):
    """False when the Localisation column names another library: a BnF shelfmark would then be wrong."""
    place = row.get("Localisation")
    return pd.isna(place) or "bnf" in place.lower() or "nationale de france" in place.lower()


def fill_empty(df, index, values):
    """Write the values in the empty cells of the row only; returns the number of filled cells."""
    filled = 0
    for column, value in values.items():
        if value is not None and column in df.columns and pd.isna(df.at[index, column]):
            df.at[index, column] = value
            filled += 1
    return filled


def progress():
    return Progress(TextColumn("[bold]{task.description:<15}"), BarColumn(), MofNCompleteColumn(),
                    TimeElapsedColumn(), console=console)


def show_header(filename, df, fmt, objet, geonames_enabled):
    grid = Table.grid(padding=(0, 2))
    grid.add_row("Fichier", Text(str(filename), style="bold"))
    separator = "tabulation" if fmt.sep == "\t" else f"« {fmt.sep} »"
    grid.add_row("Contenu", f"{len(df)} lignes · séparateur {separator}")
    grid.add_row("Notices", "personnes (autorités BnF)" if objet == "PERS" else "livres (notices bibliographiques BnF)")
    grid.add_row("GeoNames", "activé" if geonames_enabled else "[yellow]désactivé[/] (variable GEONAME_USERNAME absente)")
    console.print(Panel.fit(grid, title="[bold]UniMatic2CSV[/]", border_style="blue"))


def show_issues(issues, report):
    table = Table(title=f"Lignes à vérifier ({len(issues)})", title_justify="left", title_style="bold yellow",
                  box=box.SIMPLE_HEAD)
    table.add_column("Ligne", style="bold", no_wrap=True)
    table.add_column("Problème", style="yellow", no_wrap=True)
    table.add_column("ARK / notice BnF", no_wrap=True, overflow="ellipsis", max_width=max(20, console.width - 48))
    for row, ark, problem, detail in issues[:MAX_ISSUES_SHOWN]:
        table.add_row(Text(str(row)), problem, Text(f"{ark}  {detail}" if detail else str(ark)))
    if len(issues) > MAX_ISSUES_SHOWN:
        table.caption = f"… et {len(issues) - MAX_ISSUES_SHOWN} autres : liste complète dans {report}"
    console.print(table)


def show_summary(stats):
    def warn(count):
        return f"[yellow]{count}[/]" if count else "0"

    table = Table(title="Résumé", title_justify="left", title_style="bold", show_header=False, box=box.ROUNDED)
    table.add_column()
    table.add_column(justify="right")
    table.add_row("Cellules remplies", f"[bold green]{stats['filled']}[/]")
    table.add_row("Lignes enrichies", str(stats["rows"]))
    if stats["isni"] is not None:
        table.add_row("ISNI complétés (zéros initiaux)", str(stats["isni"]))
    table.add_row("Lignes sans ARK BnF", str(stats["no_ark"]))
    table.add_row("Notices introuvables", warn(stats["not_found"]))
    table.add_row("Lignes ignorées (nom/titre ≠ notice)", warn(stats["mismatch"]))
    console.print(table)


@click.command()
@click.argument("filename", type=click.Path(exists=True, dir_okay=False))
@click.argument("objet", type=click.Choice(["PERS", "BOOK"], case_sensitive=False))
@click.option("-h", "--header", "header", type=int, default=0, help="Numéro de la ligne d'en-tête.")
@click.option("-o", "--output", type=click.Path(dir_okay=False),
              help="Fichier de sortie (par défaut : FILENAME, après une copie en FILENAME.bak).")
@click.option("--no-check", is_flag=True,
              help="Enrichir aussi les lignes dont le nom / titre abrégé diffère de la notice BnF.")
def run(filename: str, objet: str, header: int, output: str, no_check: bool):
    """Complète les cellules vides de FILENAME avec les notices BnF de sa colonne ARK.

    OBJET : PERS pour les fiches personnes, BOOK pour les fiches livres.
    """
    objet = objet.upper()
    notice_class = NOTICES[objet]
    df, fmt = read_csv(filename, header)
    if "ARK" not in df.columns:
        raise click.UsageError(f"Pas de colonne ARK dans {filename}.")
    geonames = GeoNames(os.environ.get("GEONAME_USERNAME"))
    show_header(filename, df, fmt, objet, geonames.enabled)

    arks = df["ARK"].map(normalize_ark)
    issues = []  # (row, ARK, problem, detail)
    for index in df.index[df["ARK"].notna() & arks.isna()]:
        issues.append((row_label(df, index, header), df.at[index, "ARK"], "hors catalogue BnF", ""))
    duplicated = arks[arks.notna() & arks.duplicated(keep=False)]
    for ark, rows in duplicated.groupby(duplicated):
        labels = ", ".join(str(row_label(df, i, header)) for i in rows.index)
        issues.append((labels, ark, "ARK en double", ""))

    sru = SRU()
    unique_arks = list(dict.fromkeys(arks.dropna()))
    with progress() as bar:
        task = bar.add_task("Catalogue BnF", total=len(unique_arks))
        records = sru.fetch(unique_arks, objet, advance=lambda count: bar.advance(task, count))
    if sru.unavailable:
        console.print(Text(f"Le catalogue BnF ne répond plus ({sru.unavailable}) : les notices déjà reçues sont "
                           "utilisées, relancez plus tard pour les autres.", style="yellow"))

    stats = {"filled": 0, "rows": 0, "no_ark": 0, "not_found": 0, "mismatch": 0, "isni": None}
    try:
        with progress() as bar:
            for index, ark in bar.track(arks.items(), total=len(arks), description="Enrichissement"):
                label = row_label(df, index, header)
                if ark is None:
                    stats["no_ark"] += 1
                    continue
                if ark not in records:
                    issues.append((label, ark, "introuvable", sru.errors.get(ark, "")))
                    stats["not_found"] += 1
                    continue

                notice = notice_class(records[ark])
                if isinstance(notice, Person) and not notice.is_person():
                    issues.append((label, ark, "notice d'œuvre", "l'ARK ne désigne pas une personne"))
                    stats["mismatch"] += 1
                    continue
                if isinstance(notice, Book) and notice.reproduction():
                    issues.append((label, ark, "reproduction", "microforme ou fac-similé : lieu et date non repris"))
                if not no_check and not matches(df.loc[index], notice):
                    issues.append((label, ark, "nom/titre différent", notice.labels()[0]))
                    stats["mismatch"] += 1
                    continue

                values = notice.to_dict()
                if not bnf_copy(df.loc[index]):
                    values.pop("Cote", None)
                filled = fill_empty(df, index, values)
                for place, id_column in notice.PLACES.items():
                    if place in df.columns and id_column in df.columns and pd.isna(df.at[index, id_column]):
                        filled += fill_empty(df, index, {id_column: geonames.get_id(df.at[index, place])})
                stats["filled"] += filled
                stats["rows"] += filled > 0
    except KeyboardInterrupt:
        console.print("[yellow]Interrompu : les lignes déjà traitées sont enregistrées.[/]")

    if "ISNI" in df.columns:
        isni = df["ISNI"].map(normalize_isni)
        stats["isni"] = int((isni.fillna("") != df["ISNI"].fillna("")).sum())
        df["ISNI"] = isni

    backup = None
    if output is None:
        output, backup = filename, f"{filename}.bak"
        shutil.copy2(filename, backup)
    write_csv(df, output, fmt)

    report = None
    if issues:
        report = Path(output).with_name(f"{Path(output).stem}_a_verifier.csv")
        write_csv(pd.DataFrame(issues, columns=["Ligne", "ARK", "Probleme", "Detail"]), report, fmt)
        show_issues(issues, report)

    show_summary(stats)
    console.print(Text.assemble(("✔ ", "green"), "Fichier écrit : ", (str(output), "bold"),
                                f"  (sauvegarde : {backup})" if backup else ""))
    if report:
        console.print(Text.assemble(("! ", "yellow"), "Lignes à vérifier : ", (str(report), "bold")))


if __name__ == "__main__":
    run()
