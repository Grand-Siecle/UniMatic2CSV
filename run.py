import click
import pandas as pd
import numpy as np

from src.person import Person
from src.book import Book
from src.opt.tools import check_ark


@click.command()
@click.argument('filename', type=click.Path(exists=True))
@click.argument('objet', type=click.Choice(['PERS', 'BOOK'], case_sensitive=False))
def run(filename: str, objet: str):
    # Read csv
    df = pd.read_csv(filename, delimiter=';', header=1)
    df = df.astype(str)

    for index, row in df.iterrows():

        try:
            ark = row['ARK'].strip()

            if check_ark(ark):
                if objet == 'PERS':
                    pers = Person(ark)

                    # request
                    id_data = pers.id_data()
                    life_data = pers.life_data()
                    activity_data = pers.activity_data()

                    dict_fusion = {**id_data, **life_data, **activity_data}

                elif objet == 'BOOK':
                    book = Book(ark)

                    # request
                    id_author = book.id_author()
                    get_title = book.get_title()
                    get_publication = book.get_publication()
                    get_matiere = book.get_matiere()

                    dict_fusion = {**id_author, **get_title, **get_publication, **get_matiere}

                else:
                    raise ValueError('You need to define the csv object')
                # Replace null or NaN values in the row
                for key, value in dict_fusion.items():
                    if pd.notna(df.at[index, key]):  # Check if the cell is not empty
                        df.at[index, key] = value
                        print(df.at[index, key])
            else:
                click.echo(f'\033[31mImpossible to parse row with index : {str(index)}\x1b[31m')
        except Exception as err:
            click.echo(f'\033[31mImpossible to parse row with index : {str(index)}, error: {str(err)}.\x1b[31m')

    df.to_csv(filename, sep=';', index=False, encoding='utf-8')

if __name__ == '__main__':
    run()