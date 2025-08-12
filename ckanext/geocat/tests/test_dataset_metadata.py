"""Tests for metadata"""

import json
import os
import unittest
from pprint import pprint

from ckanext.geocat.utils import csw_mapping

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))


class TestGeocatDcatDatasetMetadata(unittest.TestCase):
    def setUp(self):
        self.csw_map = csw_mapping.GeoMetadataMapping(
            organization_slug="swisstopo",
            geocat_perma_link="https://perma-link/",
            geocat_perma_label="some label",
            legal_basis_url="",
            default_rights="",
            valid_identifiers=["8454f7d9-e3f2-4cc7-be6d-a82196660ccd@swisstopo"],
        )
        self.geocat_identifier = "93814e81-2466-4690-b54d-c1d958f1c3b8"

    def _load_xml(self, filename):
        path = os.path.join(__location__, "fixtures", filename)
        with open(path) as xml:
            entry = xml.read()
        return entry

    def _is_multi_lang(self, value):
        for lang in ["de", "fr", "it", "en"]:
            assert lang in value

    def test_fields(self):
        xml = self._load_xml("testdata-deprecated-protocols.xml")
        dataset = self.csw_map.get_metadata(xml, self.geocat_identifier)

        fields = [
            "identifier",
            "title",
            "description",
            "issued",
            "modified",
            "publisher",
            "contact_points",
            "groups",
            "language",
            "relations",
            "temporals",
            "keywords",
            "url",
            "spatial",
            "coverage",
            "accrual_periodicity",
            "qualified_relations",
            "owner_org",
            "resources",
            "conforms_to",
        ]

        for field in fields:
            assert field in dataset

        # make sure only the defined fields are on the dataset
        assert sorted(fields) == sorted(dataset.keys())

        for key, value in dataset.items():
            pprint(value)
            assert key in fields

        # check multilang fields
        self._is_multi_lang(dataset.get("title"))
        self._is_multi_lang(dataset.get("description"))

    def test_fields_values(self):
        xml = self._load_xml("testdata-deprecated-protocols.xml")
        dataset = self.csw_map.get_metadata(xml, self.geocat_identifier)

        # identifier
        assert "93814e81-2466-4690-b54d-c1d958f1c3b8@swisstopo" == dataset.get(
            "identifier"
        )

        # title

        assert "L\xe4rmbelastung durch Eisenbahnverkehr Nacht" == dataset["title"]["de"]
        assert (
            "Exposition au bruit du trafic ferroviaire, nuit" == dataset["title"]["fr"]
        )
        assert (
            "Esposizione al rumore del traffico ferroviario, notte"
            == dataset["title"]["it"]
        )
        assert "Nighttime railway noise exposure" == dataset["title"]["en"]

        # description
        assert (
            "Die Karte zeigt, welcher L\xe4rmbelastung" in dataset["description"]["de"]
        )
        assert "" in dataset["description"]["fr"]
        assert "" in dataset["description"]["it"]
        assert "" in dataset["description"]["en"]

        # dates
        issued_modified_date = "2011-12-31T00:00:00"
        assert issued_modified_date == dataset["issued"]
        assert issued_modified_date == dataset["modified"]

        # publisher
        publisher = json.loads(dataset["publisher"])
        assert isinstance(publisher, dict)
        assert "Bundesamt f\xfcr Umwelt" == publisher["name"]["de"]
        assert "http://www.bafu.admin.ch/abteilung-laerm-nis" == publisher["url"]

        # contact points
        assert hasattr(dataset["contact_points"], "__iter__")
        assert 1 == len(dataset["contact_points"])
        for contact_point in dataset["contact_points"]:
            assert "noise@bafu.admin.ch" == contact_point["name"]
            assert "noise@bafu.admin.ch" == contact_point["email"]

        # groups
        groups = ["regi", "envi"]
        for group in dataset.get("groups"):
            assert group["name"] in groups

        # language
        assert {"http://publications.europa.eu/resource/authority/language/DEU"} == set(
            dataset.get("language")
        )

        # conforms to
        assert [
            "https://www.vs.ch/documents/17311/472431/Reserves_forestieres_Catalogue_objets"
        ] == dataset["conforms_to"]
        assert 1 == len(dataset["conforms_to"])
        assert isinstance(dataset["conforms_to"], list)

        # resources
        assert hasattr(dataset["resources"], "__iter__")
        assert 4 == len(dataset["resources"])
        for relation in dataset["resources"]:
            assert relation["title"] is not None
            assert relation["description"] is not None
            # Node with protocol OPENDATA:SWISS should not be mapped
            assert relation["description"] != "Permalink to dataset on opendata.swiss"
            assert relation["url"] is not None

        # keywords
        keywords = {
            "de": [
                "larmbekampfung",
                "larmbelastung",
                "larmpegel",
                "larmimmission",
                "verkehrslarm",
                "larmwirkung",
                "gesundheit-und-sicherheit",
                "e-geoch-geoportal",
            ],
            "fr": [
                "impact-du-bruit",
                "effet-du-bruit",
                "diminution-du-bruit",
                "niveau-sonore",
                "polluant-sonore",
                "sante-et-securite-des-personnes",
                "geoportail-e-geoch",
                "bruit-routier",
            ],
            "it": [
                "livello-del-rumore",
                "inquinante-acustico",
                "rumore-del-traffico",
                "effetto-del-rumore",
                "geoportale-e-geoch",
                "abbattimento-del-rumore",
                "salute-umana-e-sicurezza",
                "immissione-di-rumore",
            ],
            "en": [
                "noise-pollutant",
                "noise-level",
                "noise-abatement",
                "noise-immission",
                "human-health-and-safety",
                "traffic-noise",
                "noise-effect",
                "e-geoch-geoportal",
            ],
        }
        for lang in ["de", "fr", "it", "en"]:
            assert set(keywords[lang]) == set(dataset["keywords"][lang])

        # url
        assert "http://www.bafu.admin.ch/laerm/" == dataset.get("url")

        # spatial
        assert "Schweiz" == dataset.get("spatial")

        # coverage
        assert "" == dataset.get("coverage")

        # accrual periodicity
        assert "" == dataset.get("accrual_periodicity")

        # qualified relations
        assert hasattr(dataset["qualified_relations"], "__iter__")
        assert 1 == len(dataset["qualified_relations"])
        assert {
            "relation": "http://test.ckan.net/perma/8454f7d9-e3f2-4cc7-be6d-a82196660ccd@swisstopo",
            "had_role": "http://www.iana.org/assignments/relation/related",
        } == dataset["qualified_relations"][0]

    def test_fields_values_de_only(self):
        xml = self._load_xml("only_de.xml")
        dataset = self.csw_map.get_metadata(xml, self.geocat_identifier)

        # identifier
        assert "93814e81-2466-4690-b54d-c1d958f1c3b8@swisstopo" == dataset.get(
            "identifier"
        )

        # title
        assert "L\xe4rmbelastung durch Eisenbahnverkehr Nacht" == dataset["title"]["de"]
        assert "" == dataset["title"]["fr"]
        assert "" == dataset["title"]["it"]
        assert "" == dataset["title"]["en"]

        # description
        assert (
            "Die Karte zeigt, welcher L\xe4rmbelastung" in dataset["description"]["de"]
        )
        assert "" in dataset["description"]["fr"]
        assert "" in dataset["description"]["it"]
        assert "" in dataset["description"]["en"]

        # language
        assert set(
            ["http://publications.europa.eu/resource/authority/language/DEU"]
        ) == set(dataset.get("language"))

        # keywords
        keywords = {
            "de": [
                "larmbekampfung",
                "larmbelastung",
                "larmpegel",
                "larmimmission",
                "verkehrslarm",
                "larmwirkung",
                "gesundheit-und-sicherheit",
                "e-geoch-geoportal",
            ],
            "fr": [],
            "it": [],
            "en": [],
        }
        for lang in ["de", "fr", "it", "en"]:
            assert set(keywords[lang]) == set(dataset["keywords"][lang])

    def test_date_revision(self):
        xml = self._load_xml("revision_date.xml")
        dataset = self.csw_map.get_metadata(xml, self.geocat_identifier)

        revision_date = "2011-12-31T00:00:00"
        assert revision_date == dataset["issued"]
        assert revision_date == dataset["modified"]

    def test_date_publication(self):
        xml = self._load_xml("publication_date.xml")
        dataset = self.csw_map.get_metadata(xml, self.geocat_identifier)

        assert "2010-12-30T00:00:00" == dataset["issued"]
        assert "2011-12-31T00:00:00" == dataset["modified"]

        assert dataset["issued"] != dataset["modified"]

    def test_date_issued_before_1900(self):
        xml = self._load_xml("publication_date_before_1900.xml")
        dataset = self.csw_map.get_metadata(xml, self.geocat_identifier)

        assert dataset["issued"] == "1891-12-30T00:00:00"
        assert dataset["modified"] == "1891-12-31T00:00:00"

    def test_documentation(self):
        xml = self._load_xml("geocat-testdata.xml")
        dataset = self.csw_map.get_metadata(xml, self.geocat_identifier)

        assert sorted(dataset["documentation"]) == [
            "https://example.org/documentation/1",
            "https://example.org/documentation/2",
        ]


if __name__ == "__main__":
    unittest.main()
