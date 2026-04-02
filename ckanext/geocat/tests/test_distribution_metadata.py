"""Distribution tests: DCAT-AP-CH (dcat_mapping) and CHE/ISO (csw_mapping)."""

import os
import unittest

from ckanext.geocat.utils import csw_mapping, dcat_mapping

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


# ---------------------------------------------------------------------------
# CHE / ISO19139.che — csw_mapping.GeoMetadataMapping
# ---------------------------------------------------------------------------

LANGUAGES = ["de", "fr", "it", "en"]


class TestGeocatDistributionProtocols(unittest.TestCase):
    def setUp(self):
        self.distributions = []

    def _set_csw(self):
        return csw_mapping.GeoMetadataMapping(
            organization_slug="swisstopo",
            geocat_perma_link="https://perma-link/",
            geocat_perma_label="some label",
            legal_basis_url="",
            default_rights="",
            valid_identifiers=["8454f7d9-e3f2-4cc7-be6d-a82196660ccd@swisstopo"],
        )

    def _load_xml(self, filename):
        path = os.path.join(__location__, "fixtures", filename)
        with open(path) as xml:
            entry = xml.read()
        return entry

    def _is_multi_lang(self, value):
        for lang in LANGUAGES:
            assert lang in value

    def _get_distribution_by_protocol(self, protocol):
        for distribution in self.distributions:
            if distribution.get("protocol") == protocol:
                return distribution


class TestGeocatDeprecatedDistributionProtocols(TestGeocatDistributionProtocols):
    def setUp(self):
        csw_map = self._set_csw()
        xml = self._load_xml("testdata-deprecated-protocols.xml")
        geocat_identifier = "93814e81-2466-4690-b54d-c1d958f1c3b8"
        self.dataset = csw_map.get_metadata(xml, geocat_identifier)
        self.distributions = self.dataset.get("resources")

    def test_resources_are_picked_up_correctly_with_dataset_fields(self):
        assert 4 == len(self.distributions)
        for distribution in self.distributions:
            assert (
                distribution.get("rights")
                == "https://opendata.swiss/terms-of-use#terms_open"
            )
            assert (
                distribution.get("license")
                == "https://opendata.swiss/terms-of-use#terms_open"
            )

            assert distribution.get("issued") == self.dataset.get("issued")
            assert distribution.get("modified") == self.dataset.get("modified")
            self._is_multi_lang(distribution["title"])
            self._is_multi_lang(distribution["description"])

    def test_deprecated_WWW_DOWNLOAD_protocol_is_mapped_to_download_resource(
        self,
    ):
        deprecated_download_protocol = "WWW:DOWNLOAD-1.0-http--download"
        distribution = self._get_distribution_by_protocol(deprecated_download_protocol)
        assert distribution is not None
        assert distribution.get("protocol") == deprecated_download_protocol
        assert distribution.get("url") == distribution.get("download_url")
        assert distribution.get("media_type") is not None

    def test_deprecated_WMS_protocol(self):
        deprecated_wms_protocol = "OGC:WMS-http-get-capabilities"
        distribution = self._get_distribution_by_protocol(deprecated_wms_protocol)
        assert distribution.get("protocol") == deprecated_wms_protocol
        assert distribution is not None
        assert distribution.get("download_url") is None
        assert distribution.get("format") == "WMS"
        assert distribution.get("media_type") is None

    def test_deprecated_WMTS_protocol(self):
        deprecated_wmts_protocol = "OGC:WMTS-http-get-capabilities"
        distribution = self._get_distribution_by_protocol(deprecated_wmts_protocol)
        assert distribution.get("protocol") == deprecated_wmts_protocol
        assert distribution is not None
        assert distribution.get("download_url") is None
        assert distribution.get("format") == "WMTS"
        assert distribution.get("media_type") is None

    def test_deprecated_download_url_protocol(self):
        deprecated_download_url_protocol = "WWW:DOWNLOAD-URL"
        distribution = self._get_distribution_by_protocol(
            deprecated_download_url_protocol
        )
        assert distribution is not None
        assert distribution.get("protocol") == deprecated_download_url_protocol
        assert distribution.get("url") == distribution.get("download_url")


class TestGeocatNormedDistributionProtocols(TestGeocatDistributionProtocols):
    def setUp(self):
        csw_map = self._set_csw()
        xml = self._load_xml("geocat-testdata.xml")
        geocat_identifier = "3143e92b-51fa-40ab-bcc0-fa389807e879"
        self.dataset = csw_map.get_metadata(xml, geocat_identifier)
        self.distributions = self.dataset.get("resources")

    def test_fields_that_come_from_the_dataset(self):
        assert 6 == len(self.distributions)
        for distribution in self.distributions:
            assert (
                distribution.get("rights")
                == "https://opendata.swiss/terms-of-use#terms_by"
            )
            assert (
                distribution.get("license")
                == "https://opendata.swiss/terms-of-use#terms_by"
            )
            assert distribution.get("issued") == self.dataset.get("issued")
            assert distribution.get("modified") == self.dataset.get("modified")
            self._is_multi_lang(distribution["title"])
            self._is_multi_lang(distribution["description"])

    def test_normed_protocol_WWW_DOWNLOAD_APP(self):
        download_app_protocol = "WWW:DOWNLOAD-APP"
        distribution = self._get_distribution_by_protocol(download_app_protocol)
        assert distribution.get("url") is not None
        assert distribution.get("download_url") is None
        assert "SERVICE" == distribution.get("format")

    def test_normed_protocol_OGC_WMS_without_gmd_name(self):
        ogc_wms_protocol = "OGC:WMS"
        distribution = self._get_distribution_by_protocol(ogc_wms_protocol)
        assert distribution is not None
        assert distribution.get("url") is not None
        assert distribution.get("download_url") is None
        assert "WMS" == distribution.get("format")
        assert "" == distribution["title"]["de"]
        assert "" == distribution["title"]["en"]
        assert "" == distribution["title"]["fr"]
        assert "" == distribution["title"]["it"]

    def test_normed_protocol_Map_Preview(self):
        map_preview_protocol = "MAP:Preview"
        distribution = self._get_distribution_by_protocol(map_preview_protocol)
        assert distribution is not None
        assert distribution["protocol"] == map_preview_protocol
        for lang in LANGUAGES:
            assert distribution["title"][lang].startswith("Map (Preview)")
        assert distribution.get("url") is not None
        assert distribution.get("download_url") is None
        assert "SERVICE" == distribution.get("format")
        assert "Map (Preview) Kartenvorschau" == distribution["title"]["de"]
        assert "Map (Preview)" == distribution["title"]["en"]
        assert "Map (Preview)" == distribution["title"]["fr"]
        assert "Map (Preview)" == distribution["title"]["it"]

    def test_normed_protocol_ESRI_REST(self):
        esri_rest_protocol = "ESRI:REST"
        distribution = self._get_distribution_by_protocol(esri_rest_protocol)
        assert distribution is not None
        assert distribution.get("url") is not None
        assert distribution.get("download_url") is None
        assert "API" == distribution.get("format")
        assert "RESTful API von geo.admin.ch" == distribution["title"]["de"]
        assert "" == distribution["title"]["en"]
        assert "" == distribution["title"]["fr"]
        assert "" == distribution["title"]["it"]

    def test_normed_protocol_WWW_DOWNLOAD_with_format_INTERLIS(self):
        download_protocol_with_format = "WWW:DOWNLOAD:INTERLIS"
        distribution = self._get_distribution_by_protocol(download_protocol_with_format)
        assert distribution is not None
        assert distribution.get("url") == distribution.get("download_url")
        assert "INTERLIS" == distribution.get("media_type")


if __name__ == "__main__":
    unittest.main()
