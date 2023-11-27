# -----------------------------------------------------------
# Code inspired by: Kelly Christensen
# Repository: https://github.com/kat-kel/alto2tei.git
# Python class to parse and store data from the BNF's general catalogue.
# -----------------------------------------------------------


from lxml import etree
import requests


class SRU(object):
    NS = {"s": "http://www.loc.gov/zing/srw/", "m": "info:lc/xmlns/marcxchange-v2"}

    def __init__(self, ark: str):
        """Args:
            ark (string): document ARK in BnF catalogue"""
        self.ark = ark

    def request(self, mode: str):
        """Request metadata from the BnF's SRU API.

        mode :
        Returns:
            root (etree_Element): parsed XML tree of requested Unimarc data
            perfect_match (boolean): True if request was completed with Gallica ark / directory basename
        """

        if mode == 'PERS':
            r = requests.get(
            f'https://catalogue.bnf.fr/api/SRU?version=1.2&operation=searchRetrieve&query=aut.persistentid%20all%20%20"{self.ark}"')
        elif mode == 'BOOK':
            r = requests.get(
                f'https://catalogue.bnf.fr/api/SRU?version=1.2&operation=searchRetrieve&query=bib.persistentid%20all%20%20"{self.ark}"')
        else:
            raise ValueError('Verify mode value error')

        root = etree.fromstring(r.content)
        if root.find('.//s:numberOfRecords', namespaces=self.NS).text == "0":
            perfect_match = False
            print(f"|        \33[31mdid not find digitised document in BnF catalogue\x1b[0m")
        else:
            perfect_match = True
            print(f"|        \33[32mfound digitised document in BnF catalogue\x1b[0m")
        return root, perfect_match
