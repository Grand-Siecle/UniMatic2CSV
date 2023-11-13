import numpy as np

from src.base import SRU


class Person(SRU):
    def __init__(self, ark):
        super().__init__(ark)
        self.root, self.perfect_match = self.request()

    def id_data(self):
        fields = ["isni"]
        
        data = {}
        {data.setdefault(f, np.NAN) for f in fields}

        author_element = self.root.find('.//m:datafield[@tag="100"][@code="o"]', namespaces=self.NS)

        # -- identifier (700s subfield "o") --
        has_isni = author_element.find('m:subfield[@code="o"]', namespaces=self.NS)
        if has_isni is not None and has_isni.text[0:4] == "ISNI":
            data["isni"] = has_isni.text[4:]