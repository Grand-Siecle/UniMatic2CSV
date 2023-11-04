import re
import click

from src.opt.variables import ARK


def check_ark(ctx, param, ark):
    """Checks the validity of a ARK id with regex for a CLI argument"""

    regex = ARK

    try:
        if re.match(regex, ark):
            return ark
        else:
            raise click.BadParameter(f"Valeur invalide pour l'argument {ark}. La valeur ne correspond pas à un identifiant ARK")

    except re.error as e:
        raise click.BadParameter(f"Expression régulière invalide : {regex}")