import click

from src.base import SRU
from src.person import Person
from src.opt.tools import check_ark


@click.command()
@click.argument("ark", type=str, callback=check_ark)
def run(ark):
    person = Person(ark)
    person.basic_data()


if __name__ == '__main__':
    run()
