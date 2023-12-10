import click
import pandas as pd
import numpy as np

from src.person import Person
from src.book import Book
from src.opt.tools import check_ark


@click.command()
@click.argument('filename', type=click.Path(exists=True))
@click.option('--type', type=click.Choice(['PERS', 'BOOK'], case_sensitive=False))
def run(filename, type):
    # Read csv
    df = pd.read_csv(filename, delimiter=';')

    for index, row in df.iterrows():
        #
        ark = row['Identifiant_ark']

        def replace_value(**kwargs):
            for key, value in kwargs.items():
                if row[key].isnull() or row[key] == np.NAN:
                    return value
                else:
                    pass

        if check_ark(ark):
            if type == 'PERS':
                pers = Person(ark)

                # request
                id_data = pers.id_data()
                life_data = pers.life_data()
                activity_data = pers.activity_data()

                dict_fusion = {**id_data, **life_data, **activity_data}

            elif type == 'BOOK':
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
            df.loc[index] = df.loc[index].apply(replace_value, **dict_fusion)
        else:
            click.echo(f'Impossible to parse row with index : {str(index)}')
            pass

    df.to_csv(filename, index=False)

if __name__ == '__main__':
    run()