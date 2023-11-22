import click

from src.base import SRU
from src.person import Person
from src.opt.tools import check_ark


@click.command()
@click.argument("ark", type=str, callback=check_ark)
def run(ark):
    person = Person(ark)
    id_person = person.id_data()
    lifeTime_person = person.life_data()


if __name__ == '__main__':
    run()
