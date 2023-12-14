import re
import click
import requests
import os
from src.opt.variables import ARK


def check_ark(ark):
    """Checks the validity of a ARK id with regex for a CLI argument"""

    regex = ARK

    try:
        if re.match(regex, ark):
            return ark
        else:
            raise click.BadParameter(f"Valeur invalide pour l'argument {ark}. La valeur ne correspond pas à un identifiant ARK")

    except re.error as e:
        raise click.BadParameter(f"Expression régulière invalide : {regex}")


def get_geonames_id(location_name):

    """
    Obtient l'identifiant (ID) d'un lieu à partir de son nom en utilisant l'API Geonames.

    Args:
        location_name (str): Le nom du lieu.
        username (str): Votre nom d'utilisateur Geonames (nécessaire pour l'authentification).

    Returns:
        int or None: L'identifiant (ID) du lieu, ou None si la requête échoue.
    """
    base_url = "http://api.geonames.org/searchJSON"
    try:
        username = os.environ['GEONAME_USERNAME']
    except KeyError:
        click.echo("Vous devez indiquer votre nom d'utilisateur Geoname au sein de la variable d'environnement [GEONAME_USERNAME]")
        exit()

    # Paramètres de la requête
    params = {
        'q': location_name,
        'maxRows': 1,  # Vous pouvez ajuster cela en fonction de vos besoins
        'username': username,  # Remplacez par votre nom d'utilisateur Geonames
    }

    try:
        # Effectuer la requête
        response = requests.get(base_url, params=params)
        data = response.json()

        # Extraire l'ID du premier résultat (si disponible)
        geonames_id = data['geonames'][0]['toponymName'] if 'geonames' in data and data['geonames'] else None
        return geonames_id

    except requests.RequestException as e:
        return None
