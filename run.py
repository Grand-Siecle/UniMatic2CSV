import click

from src.person import Person
from src.book import Book
from src.opt.tools import check_ark


@click.command()
@click.argument("ark", type=str, callback=check_ark)
def run(ark):
    book = Book(ark)
    book.get_title()
    lifeTime_person = book.get_matiere()
    print(lifeTime_person)


if __name__ == '__main__':
    run()
