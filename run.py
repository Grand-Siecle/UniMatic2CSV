import click

from src.base import SRU
from src.opt.tools import check_ark


@click.command()
@click.argument("ark", type=str, callback=check_ark)
def run(ark):
    print(ark)
    sru = SRU(ark)
    url, root, perfect_match = sru.request()

    click.echo(url)
    click.echo(root)
    click.echo("******************************************************")
    click.echo(perfect_match)


if __name__ == '__main__':
    run()
