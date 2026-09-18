from src.book import Book
from src.person import Person


def test_person_full_dates_without_places(record):
    data = Person(record("aut_cb12230181h")).to_dict()
    assert data["ISNI"] == "0000000118738159"
    assert data["Annee_naissance"] == "1586/05/22"
    assert data["Annee_mort"] == "1658/03/12"
    assert data["Ville_naissance"] is None and data["Ville_mort"] is None
    assert data["Professions"].endswith("Imprimeur-libraire")


def test_person_places_and_several_notes(record):
    person = Person(record("aut_cb12083793k"))
    data = person.to_dict()
    assert person.labels()[0] == "Alberti"
    assert data["Ville_naissance"] == "Gênes (Italie)"
    assert data["Ville_mort"] == "Rome (Italie)"
    assert data["Professions"] == "A aussi écrit en latin|Architecte, sculpteur, musicien humaniste"


def test_person_partial_dates(record):
    # 103 $a " 16..      165.     " : the old code split on double spaces and lost the death date
    data = Person(record("aut_cb123854974")).to_dict()
    assert data["Annee_naissance"] == "16.."
    assert data["Annee_mort"] == "165."
    assert data["ISNI"] == "0000000139923695"


def test_person_uncertain_birth_date(record):
    # 103 $a " 1604    ? 16780329 "
    data = Person(record("aut_cb12259347g")).to_dict()
    assert data["Annee_naissance"] == "1604?"
    assert data["Annee_mort"] == "1678/03/29"
    assert data["Ville_mort"] == "Dax (Landes)"


def test_book_format_in_210_and_digitised_shelfmark(record):
    data = Book(record("bib_cb31721367g")).to_dict()
    assert data["Titre_long"].startswith("La Perpetuelle croix")
    assert data["Format"] == "in-seize"  # "in-16" written in 210 $d
    assert data["Lieu_publication"] == "Paris"
    assert data["Date_01"] == "1659"
    assert data["Sujet"] is None
    assert data["Cote"] == "NUMM-859716"


def test_book_without_210(record):
    data = Book(record("bib_cb393163358")).to_dict()
    assert data["Lieu_publication"] == "Paris"  # 620 $d
    assert data["Date_01"] == "1660"  # 100 $a
    assert data["Format"] == "in-quarto"
    assert data["Sujet"] == "Dessin d'anatomie"
    assert data["Cote"] == "NUMM-1518666"


def test_book_format_in_215a_and_no_digitised_copy(record):
    data = Book(record("bib_cb312129210")).to_dict()
    assert data["Format"] == "in-octavo"  # "In-8° , pièce limin., ..."
    assert data["Date_01"] == "1598"  # 210 $d is "1598. 2e éd."
    assert data["Cote"] == "D-50578"


def test_book_reproduction_keeps_no_place_nor_date(record):
    book = Book(record("bib_cb35153778v"))  # microfiche (1972) of "Le Parnasse alarmé" (1649)
    data = book.to_dict()
    assert book.reproduction()
    assert data["Lieu_publication"] is None and data["Date_01"] is None
    assert data["Format"] is None  # "105x148 mm" is not a format of the CSV vocabulary


def test_book_without_place_nor_year(record):
    data = Book(record("bib_cb30092742k")).to_dict()  # [S.l.], "Imprimé ceste année"
    assert data["Lieu_publication"] is None
    assert data["Date_01"] is None
    assert data["Format"] == "in-douze"


def test_work_record_is_not_a_person(record):
    assert not Person(record("aut_cb119402398")).is_person()  # "Pascal. Pensées"
    assert Person(record("aut_cb12083793k")).is_person()


def test_person_dates_before_christ(record):
    data = Person(record("aut_cb11885977m")).to_dict()  # Cicéron: 103 "-01060103 -00431207"
    assert data["Annee_naissance"] == "-106/01/03"
    assert data["Annee_mort"] == "-43/12/07"
