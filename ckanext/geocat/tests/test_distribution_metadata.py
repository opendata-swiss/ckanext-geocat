"""Tests for DCAT-AP-CH distribution (resource) mapping (dcat_mapping.py)."""

import os
import unittest

from ckanext.geocat.utils import dcat_mapping

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))

GEOCAT_ID = "93814e81-2466-4690-b54d-c1d958f1c3b8"
ORG_SLUG = "swisstopo"
CKAN_LANGS = ["de", "fr", "it", "en"]

# EU file-type URI base
FILE_TYPE_BASE = "http://publications.europa.eu/resource/authority/file-type/"
MEDIA_TYPE_BASE = "http://www.iana.org/assignments/media-types/"


def _make_mapper(**overrides):
    defaults = dict(
        organization_slug=ORG_SLUG,
        geocat_perma_link="https://perma-link/",
        geocat_perma_label={lang: "Permalink" for lang in CKAN_LANGS},
        legal_basis_url="",
        default_rights="https://opendata.swiss/terms-of-use#terms_by",
        valid_identifiers=[f"{GEOCAT_ID}@{ORG_SLUG}"],
    )
    defaults.update(overrides)
    return dcat_mapping.DcatMetadataMapping(**defaults)


def _load_xml(filename):
    path = os.path.join(__location__, "fixtures", filename)
    with open(path) as f:
        return f.read()


class TestDcatDistributions(unittest.TestCase):
    """Test that distributions from the DCAT fixture are mapped correctly."""

    def setUp(self):
        mapper = _make_mapper()
        xml = _load_xml("geocat-dcat-testdata.xml")
        dataset = mapper.get_metadata(xml, GEOCAT_ID)
        self.distributions = dataset["resources"]
        self.dataset_issued = dataset["issued"]
        self.dataset_modified = dataset["modified"]

    def _get_by_format(self, format_suffix):
        uri = FILE_TYPE_BASE + format_suffix
        for dist in self.distributions:
            if dist.get("format") == uri:
                return dist
        return None

    def test_distribution_count(self):
        self.assertEqual(4, len(self.distributions))

    def test_all_distributions_have_url(self):
        for dist in self.distributions:
            self.assertIn("url", dist)
            self.assertIsInstance(dist["url"], str)
            self.assertTrue(dist["url"])

    def test_all_distributions_have_rights(self):
        for dist in self.distributions:
            expected = "https://opendata.swiss/terms-of-use#terms_open"
            self.assertEqual(expected, dist.get("rights"))
            self.assertEqual(expected, dist.get("license"))

    def test_all_distributions_have_issued_and_modified(self):
        for dist in self.distributions:
            self.assertEqual(self.dataset_issued, dist.get("issued"))
            self.assertEqual(self.dataset_modified, dist.get("modified"))

    def test_all_distributions_have_multilang_description(self):
        for dist in self.distributions:
            desc = dist.get("description")
            self.assertIsInstance(desc, dict)
            for lang in CKAN_LANGS:
                self.assertIn(lang, desc)

    def test_all_distributions_have_language_list(self):
        for dist in self.distributions:
            self.assertIsInstance(dist.get("language"), list)
            self.assertIn("de", dist["language"])
            self.assertIn("en", dist["language"])


class TestDcatDownloadDistribution(unittest.TestCase):
    """Test the downloadable (GPKG) distribution specifically."""

    def setUp(self):
        mapper = _make_mapper()
        xml = _load_xml("geocat-dcat-testdata.xml")
        dataset = mapper.get_metadata(xml, GEOCAT_ID)
        # Identify by presence of download_url
        self.dist = next(d for d in dataset["resources"] if d.get("download_url"))

    def test_access_url_equals_download_url(self):
        self.assertEqual(self.dist["url"], self.dist["download_url"])

    def test_download_url_is_set(self):
        self.assertEqual(
            "https://data.bafu.admin.ch/laerm/download",
            self.dist["download_url"],
        )

    def test_format_is_gpkg_uri(self):
        self.assertEqual(
            FILE_TYPE_BASE + "GPKG",
            self.dist["format"],
        )

    def test_media_type_is_uri(self):
        self.assertIn(MEDIA_TYPE_BASE, self.dist["media_type"])

    def test_title_is_multilang(self):
        title = self.dist.get("title")
        self.assertIsInstance(title, dict)
        for lang in CKAN_LANGS:
            self.assertIn(lang, title)


class TestDcatServiceDistributions(unittest.TestCase):
    """Test WMS and WMTS service distributions."""

    def setUp(self):
        mapper = _make_mapper()
        xml = _load_xml("geocat-dcat-testdata.xml")
        dataset = mapper.get_metadata(xml, GEOCAT_ID)
        # Service distributions: no download_url
        self.services = [d for d in dataset["resources"] if not d.get("download_url")]

    def test_service_distributions_have_no_download_url(self):
        for dist in self.services:
            self.assertNotIn("download_url", dist)

    def test_wms_distribution_format(self):
        wms = next(
            d for d in self.services if d.get("format") == FILE_TYPE_BASE + "WMS_SRVC"
        )
        self.assertIsNotNone(wms)
        self.assertEqual(
            "https://wms.geo.admin.ch/?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetCapabilities",
            wms["url"],
        )

    def test_wmts_distribution_format(self):
        wmts = next(
            d for d in self.services if d.get("format") == FILE_TYPE_BASE + "WMTS_SRVC"
        )
        self.assertIsNotNone(wmts)

    def test_html_preview_distribution_format(self):
        html = next(
            d for d in self.services if d.get("format") == FILE_TYPE_BASE + "HTML"
        )
        self.assertIsNotNone(html)
        self.assertIn("map.geo.admin.ch", html["url"])


class TestDcatDistributionDefaultRights(unittest.TestCase):
    """Test that default_rights is used when no license is present in the distribution."""

    FIXTURE_NO_LICENSE = """\
<?xml version="1.0" encoding="UTF-8"?>
<csw:GetRecordByIdResponse xmlns:csw="http://www.opengis.net/cat/csw/2.0.2">
  <dcat:Dataset
      xmlns:dcat="http://www.w3.org/ns/dcat#"
      xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
      xmlns:dct="http://purl.org/dc/terms/"
      rdf:about="https://example.org/ds-no-lic">
    <dct:identifier>no-license-test</dct:identifier>
    <dct:title xml:lang="de">Test</dct:title>
    <dct:issued>2020-01-01T00:00:00</dct:issued>
    <dct:modified>2020-01-01T00:00:00</dct:modified>
    <dcat:distribution>
      <dcat:Distribution>
        <dcat:accessURL rdf:resource="https://example.org/data"/>
        <dct:description xml:lang="de">Beschreibung</dct:description>
      </dcat:Distribution>
    </dcat:distribution>
  </dcat:Dataset>
</csw:GetRecordByIdResponse>
"""
    DEFAULT = "https://opendata.swiss/terms-of-use#terms_by"

    def test_default_rights_used_when_no_license(self):
        mapper = _make_mapper(default_rights=self.DEFAULT)
        dataset = mapper.get_metadata(self.FIXTURE_NO_LICENSE, "no-license-test")
        self.assertEqual(self.DEFAULT, dataset["resources"][0]["rights"])
        self.assertEqual(self.DEFAULT, dataset["resources"][0]["license"])


if __name__ == "__main__":
    unittest.main()
