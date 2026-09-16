# UniMatic2CSV

Complète des fiches CSV (personnes et livres) à partir du **catalogue général de la BnF** (API SRU, notices UNIMARC) et de **GeoNames** (identifiants de lieux).

L'outil ne remplit que les **cellules vides** : ce qui a été saisi à la main n'est jamais écrasé. On peut donc le relancer autant de fois que nécessaire sur un fichier en cours.

## Installation

Python 3.10 ou plus récent.

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Pour les identifiants GeoNames (facultatif) :

1. Créez un compte gratuit sur <https://www.geonames.org/login>.
2. Activez « Free Web Services » sur <https://www.geonames.org/manageaccount>.
3. Définissez la variable d'environnement : `export GEONAME_USERNAME=mon_identifiant`.

Sans identifiant, tout le reste est rempli et les colonnes `ID_*` restent vides.

## Utilisation

```bash
python run.py FICHIER.csv PERS    # fiches personnes (notices d'autorité)
python run.py FICHIER.csv BOOK    # fiches livres (notices bibliographiques)
```

| Option | Effet |
|---|---|
| `-o, --output FICHIER` | écrit le résultat dans un autre fichier. Par défaut, le fichier d'entrée est remplacé après une copie en `FICHIER.csv.bak`. |
| `--no-check` | enrichit aussi les lignes dont le nom ou le titre ne ressemble pas à la notice BnF (voir plus bas). |
| `-h, --header N` | numéro de la ligne d'en-tête (0 par défaut). |

Exemple :

```bash
export GEONAME_USERNAME=mon_identifiant
python run.py fiche_personne_enrich.csv PERS
```

L'affichage comprend :
- **un en-tête** : fichier, nombre de lignes, séparateur, GeoNames activé ou non ;
- **deux barres de progression** : interrogation de la BnF, puis enrichissement des lignes ;
- **un tableau des lignes à vérifier**, limité aux 20 premières : ARK hors catalogue BnF, ARK en double, notice introuvable, nom ou titre différent de la notice, notice d'œuvre au lieu d'une personne, notice de reproduction (microforme, fac-similé). La liste complète est enregistrée à côté du fichier, dans `FICHIER_a_verifier.csv` ;
- **un résumé** : cellules remplies, ISNI complétés, lignes ignorées.

Un Ctrl+C pendant l'enrichissement enregistre les lignes déjà traitées. Si le catalogue BnF ne répond plus (même après les nouvelles tentatives), l'outil arrête de l'interroger, utilise les notices déjà reçues et enregistre le fichier : il suffit de relancer plus tard.

## Fonctionnement

1. **Lecture du CSV.** Le séparateur (`;` ou tabulation), le BOM UTF-8 et les fins de ligne sont détectés, puis conservés à l'écriture. Toutes les cellules sont lues comme du texte, et les `nan` sont considérés comme des cellules vides.
2. **Colonne `ARK` obligatoire.** Elle contient un ARK du catalogue général (`ark:/12148/cb…`), seul ou dans une URL. Les autres identifiants (Archives et manuscrits, autres bibliothèques…) sont ignorés.
3. **Interrogation de la BnF.** L'outil envoie un lot de 50 ARK par requête, avec au plus une requête par seconde. Si une notice illisible côté BnF fait échouer un lot, le lot est coupé en deux jusqu'à isoler cette notice.
4. **Vérification.** Le nom de la personne (`Nom` ou `Prenoms`, comparés au nom et à ses variantes dans la notice) ou le titre abrégé (`Titre_abrege`) doit ressembler à la notice. Sinon, la ligne est **ignorée et signalée**. Cela évite d'écrire les données d'un autre livre quand la colonne `ARK` a été décalée. Les pseudonymes ou les titres très différents peuvent aussi être signalés : vérifiez-les, puis utilisez `--no-check` si besoin.
5. **Type de notice.** Dans les fiches personnes, un ARK qui désigne une œuvre (par exemple « Pascal. Pensées ») est refusé et signalé. Dans les fiches livres, une notice de reproduction (microforme, fac-similé) est signalée, et ni son lieu ni sa date ne sont repris, car ce sont ceux de la reproduction.
6. **Remplissage des cellules vides.** Les ISNI dont les zéros initiaux ont été supprimés par un tableur sont aussi remis sur 16 caractères.

### Colonnes remplies

**PERS**

| Colonne | Source |
|---|---|
| `ISNI` | 010 $a |
| `Annee_naissance`, `Annee_mort` | 103 $a, au format `AAAA/MM/JJ` (`1604?` si la date est incertaine, `16..` si elle est partielle, `-106/01/03` avant J.-C.) |
| `Ville_naissance`, `Ville_mort` | 301 $a, 301 $b |
| `ID_Ville_naissance`, `ID_Ville_mort` | GeoNames (recherche limitée au pays indiqué entre parenthèses ; un département indique la France) |
| `Professions` | 300 $a (plusieurs notes séparées par `\|`) |

**BOOK**

| Colonne | Source |
|---|---|
| `Titre_long` | 200 $a |
| `Format` | 215 $d (ou 215 $a, 210 $d), converti : `in-4` → `in-quarto`, `in-fol.` → `in-folio`… (une dimension en cm ou en mm n'est pas reprise) |
| `Lieu_publication` | 620 $d (forme normalisée), sinon 214 $a ou 210 $a (jamais « [S.l.] ») |
| `ID_Lieu_publication` | GeoNames |
| `Date_01` | 100 $a (date codée), sinon l'année de 210 $d |
| `Sujet` | 606, vedettes RAMEAU `a -- x -- y -- z` séparées par `\|` |
| `Cote` | 930 $a : les cotes des exemplaires numérisés (`NUMM-…`) s'il y en a, sinon la première cote |

## Conseils pour les fichiers

- **Dans un tableur, importez les colonnes en « Texte ».** Sinon, les ISNI perdent leurs zéros (`0000000118738159` → `118738159`) et les dates partielles sont abîmées (`159.` → `159`).
- **Triez toujours toutes les colonnes ensemble.** Une colonne `ARK` décalée associe chaque ligne à la notice d'un autre document.

## API utilisées et conditions d'utilisation

- **BnF, API SRU du catalogue général** : <https://api.bnf.fr/fr/api-sru-catalogue-general>
  - L'accès est libre, sans authentification.
  - Depuis 2014, les métadonnées sont sous [Licence Ouverte / Open Licence](https://www.bnf.fr/fr/conditions-de-reutilisations-des-donnees-de-la-bnf). Leur réutilisation est libre, à condition de **mentionner la source « Bibliothèque nationale de France » et la date de récupération**.
  - D'après les [conditions générales](https://api.bnf.fr/fr/conditions-generales-dutilisation-du-site-bnf-api-et-jeux-de-donnees), la BnF peut bloquer l'accès en cas d'usage non conforme. L'outil reste donc modéré : lots de 50 ARK, une requête par seconde, User-Agent identifié, nouvelles tentatives espacées en cas d'erreur du serveur. Les requêtes sont volontairement envoyées l'une après l'autre, jamais en parallèle.
  - Depuis juin 2026, la BnF catalogue en Intermarc NG et l'UNIMARC est obtenu par conversion : le contenu de certains champs peut évoluer.
- **GeoNames** : <https://www.geonames.org/export/>
  - Un compte gratuit dispose de 10 000 crédits par jour et 1 000 par heure (une recherche = un crédit).
  - Chaque lieu n'est demandé qu'une fois par exécution. L'outil s'arrête proprement si le compte est refusé ou si le quota est atteint.
  - Les données sont sous licence CC BY : il faut **citer GeoNames**.
  - L'outil utilise le point d'accès HTTPS `secure.geonames.org`.

## Développement

```bash
pip install -r requirements-dev.txt
python -m pytest
```

Les tests fonctionnent sans réseau : ils utilisent de vraies notices BnF enregistrées dans `tests/fixtures/`.

```
run.py               interface en ligne de commande
src/base.py          client SRU BnF (requêtes par lots) et lecture des notices UNIMARC
src/person.py        notice de personne → colonnes PERS
src/book.py          notice bibliographique → colonnes BOOK
src/geonames.py      identifiants GeoNames (avec cache)
src/csvfile.py       lecture et écriture des CSV en conservant leur format
src/console.py       console rich partagée (affichage)
src/opt/tools.py     ARK, ISNI, dates UNIMARC, comparaison nom/titre
```
