"""Tests for DCAT-AP-CH dataset metadata mapping (dcat_mapping.py)."""

import json
import os
import unittest

from ckanext.geocat.utils import dcat_mapping

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))

GEOCAT_ID = "93814e81-2466-4690-b54d-c1d958f1c3b8"
ORG_SLUG = "swisstopo"
CKAN_LANGS = ["de", "fr", "it", "en"]


def _make_mapper(**overrides):
    defaults = dict(
        organization_slug=ORG_SLUG,
        geocat_perma_link="https://perma-link/",
        geocat_perma_label={"de": "geocat Permalink", "fr": "geocat lien", "en": "geocat link", "it": "geocat link"},
        legal_basis_url="",
        default_rights="",
        valid_identifiers=[f"{GEOCAT_ID}@{ORG_SLUG}"],
    )
    defaults.update(overrides)
    return dcat_mapping.DcatMetadataMapping(**defaults)


def _load_xml(filename):
    path = os.path.join(__location__, "fixtures", filename)
    with open(path) as f:
        return f.read()


class TestDcatDatasetMetadataFields(unittest.TestCase):
    """Test that get_metadata returns exactly the expected set of top-level fields."""

    def setUp(self):
        mapper = _make_mapper()
        xml = _load_xml("geocat-dcat-testdata.xml")
        self.dataset = mapper.get_metadata(xml, GEOCAT_ID)

    def _assert_multilang(self, value):
        self.assertIsInstance(value, dict)
        for lang in CKAN_LANGS:
            self.assertIn(lang, value)

    def test_all_expected_fields_present(self):
        expected = {
            "identifier", "title", "description", "issued", "modified",
            "publisher", "contact_points", "groups", "language", "relations",
            "temporals", "keywords", "url", "spatial", "coverage",
            "accrual_periodicity", "qualified_relations", "owner_org",
            "resources", "conforms_to",
        }
        self.assertEqual(expected, set(self.dataset.keys()))

    def test_title_is_multilang(self):
        self._assert_multilang(self.dataset["title"])

    def test_description_is_multilang(self):
        self._assert_multilang(self.dataset["description"])

    def test_keywords_structure(self):
        kw = self.dataset["keywords"]
        self._assert_multilang(kw)
        for lang in CKAN_LANGS:
            self.assertIsInstance(kw[lang], list)

    def test_no_opendata_swiss_keyword(self):
        kw = self.dataset["keywords"]
        for lang in CKAN_LANGS:
            self.assertNotIn("opendata.swiss", kw[lang])

    def test_resources_is_list(self):
        self.assertIsInstance(self.dataset["resources"], list)

    def test_relations_is_list(self):
        self.assertIsInstance(self.dataset["relations"], list)


class TestDcatDatasetMetadataValues(unittest.TestCase):
    """Test specific field values produced by the DCAT mapper."""

    def setUp(self):
        mapper = _make_mapper()
        xml = _load_xml("geocat-dcat-testdata.xml")
        self.dataset = mapper.get_metadata(xml, GEOCAT_ID)

    # --- identifier ---

    def test_identifier(self):
        self.assertEqual(
            f"{GEOCAT_ID}@{ORG_SLUG}", self.dataset["identifier"]
        )

    # --- title ---

    def test_title_de(self):
        self.assertEqual(
            "Lärmbelastung durch Eisenbahnverkehr Nacht",
            self.dataset["title"]["de"],
        )

    def test_title_fr(self):
        self.assertEqual(
            "Exposition au bruit du trafic ferroviaire, nuit",
            self.dataset["title"]["fr"],
        )

    def test_title_en(self):
        self.assertEqual(
            "Nighttime railway noise exposure",
            self.dataset["title"]["en"],
        )

    # --- description ---

    def test_description_de_contains_expected_text(self):
        self.assertIn(
            "Die Karte zeigt, welcher Lärmbelastung",
            self.dataset["description"]["de"],
        )

    # --- dates ---

    def test_issued(self):
        self.assertEqual("2011-12-31T00:00:00", self.dataset["issued"])

    def test_modified(self):
        self.assertEqual("2011-12-31T00:00:00", self.dataset["modified"])

    # --- publisher ---

    def test_publisher_is_json(self):
        pub = json.loads(self.dataset["publisher"])
        self.assertIsInstance(pub, dict)
        self.assertIn("name", pub)
        self.assertIn("url", pub)

    def test_publisher_name_de(self):
        pub = json.loads(self.dataset["publisher"])
        self.assertEqual("Bundesamt für Umwelt", pub["name"]["de"])

    def test_publisher_url(self):
        pub = json.loads(self.dataset["publisher"])
        self.assertEqual("http://www.bafu.admin.ch/abteilung-laerm-nis", pub["url"])

    # --- contact points ---

    def test_contact_points_length(self):
        self.assertEqual(1, len(self.dataset["contact_points"]))

    def test_contact_point_email(self):
        cp = self.dataset["contact_points"][0]
        self.assertEqual("noise@bafu.admin.ch", cp["email"])

    # --- groups (themes) ---

    def test_groups_contain_regi_and_envi(self):
        group_names = {g["name"] for g in self.dataset["groups"]}
        self.assertIn("regi", group_names)
        self.assertIn("envi", group_names)

    # --- language ---

    def test_languages(self):
        self.assertEqual({"de", "fr", "it", "en"}, set(self.dataset["language"]))

    # --- accrual periodicity ---

    def test_accrual_periodicity_absent(self):
        # Fixture has no dct:accrualPeriodicity, so value must be ""
        self.assertEqual("", self.dataset["accrual_periodicity"])

    # --- coverage ---

    def test_coverage_is_empty(self):
        self.assertEqual("", self.dataset["coverage"])

    # --- spatial ---

    def test_spatial(self):
        self.assertEqual("Schweiz", self.dataset["spatial"])

    # --- temporals ---

    def test_temporals_empty_when_no_temporal_element(self):
        self.assertEqual([], self.dataset["temporals"])

    # --- landing page ---

    def test_url(self):
        self.assertEqual("http://www.bafu.admin.ch/laerm/", self.dataset["url"])

    # --- conforms_to ---

    def test_conforms_to(self):
        expected = [
            "https://www.vs.ch/documents/17311/472431/Reserves_forestieres_Catalogue_objets"
        ]
        self.assertEqual(expected, self.dataset["conforms_to"])

    # --- relations ---

    def test_relations_contains_permalink(self):
        urls = [r["url"] for r in self.dataset["relations"]]
        self.assertIn(
            f"https://www.geocat.ch/datahub/dataset/{GEOCAT_ID}", urls
        )

    def test_permalink_has_multilang_label(self):
        permalink = next(
            r for r in self.dataset["relations"]
            if r["url"] == f"https://www.geocat.ch/datahub/dataset/{GEOCAT_ID}"
        )
        for lang in CKAN_LANGS:
            self.assertIn(lang, permalink["label"])
            self.assertIsInstance(permalink["label"][lang], str)

    # --- resources ---

    def test_resource_count(self):
        self.assertEqual(4, len(self.dataset["resources"]))

    def test_owner_org(self):
        self.assertEqual(ORG_SLUG, self.dataset["owner_org"])


class TestDcatDatasetWithLegalBasis(unittest.TestCase):
    """Test that a configured legal_basis_url is appended to relations."""

    def test_legal_basis_appended(self):
        mapper = _make_mapper(legal_basis_url="https://example.ch/legal")
        xml = _load_xml("geocat-dcat-testdata.xml")
        dataset = mapper.get_metadata(xml, GEOCAT_ID)
        urls = [r["url"] for r in dataset["relations"]]
        self.assertIn("https://example.ch/legal", urls)


class TestDcatDatasetWithPeriodOfTime(unittest.TestCase):
    """Test that dct:temporal/dct:PeriodOfTime is mapped correctly."""

    FIXTURE_TEMPORAL = """\
<?xml version="1.0" encoding="UTF-8"?>
<csw:GetRecordByIdResponse xmlns:csw="http://www.opengis.net/cat/csw/2.0.2">
  <dcat:Dataset
      xmlns:dcat="http://www.w3.org/ns/dcat#"
      xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
      xmlns:dct="http://purl.org/dc/terms/"
      rdf:about="https://example.org/ds1">
    <dct:identifier>test-temporal-id</dct:identifier>
    <dct:title xml:lang="de">Test Temporal</dct:title>
    <dct:issued>2020-01-01T00:00:00</dct:issued>
    <dct:modified>2020-01-01T00:00:00</dct:modified>
    <dct:temporal>
      <dct:PeriodOfTime>
        <dcat:startDate>2010-01-01T00:00:00</dcat:startDate>
        <dcat:endDate>2020-12-31T00:00:00</dcat:endDate>
      </dct:PeriodOfTime>
    </dct:temporal>
  </dcat:Dataset>
</csw:GetRecordByIdResponse>
"""

    def test_temporal_period_mapped(self):
        mapper = _make_mapper()
        dataset = mapper.get_metadata(self.FIXTURE_TEMPORAL, "test-temporal-id")
        self.assertEqual(1, len(dataset["temporals"]))
        self.assertEqual("2010-01-01T00:00:00", dataset["temporals"][0]["start_date"])
        self.assertEqual("2020-12-31T00:00:00", dataset["temporals"][0]["end_date"])

    def test_temporal_end_defaults_to_start_when_omitted(self):
        xml = self.FIXTURE_TEMPORAL.replace(
            "<dcat:endDate>2020-12-31T00:00:00</dcat:endDate>", ""
        )
        mapper = _make_mapper()
        dataset = mapper.get_metadata(xml, "test-temporal-id")
        self.assertEqual(
            dataset["temporals"][0]["start_date"],
            dataset["temporals"][0]["end_date"],
        )


if __name__ == "__main__":
    unittest.main()
