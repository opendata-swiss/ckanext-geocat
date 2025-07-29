"""Tests for metadata """
import os
import time
import unittest
from datetime import datetime

from nose.tools import *  # noqa

from ckanext.geocat.utils import csw_mapping

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))

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
            self.assertIn(lang, value)

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
        self.assertEqual(4, len(self.distributions))
        for distribution in self.distributions:
            self.assertEqual(
                distribution.get("rights"),
                "https://opendata.swiss/terms-of-use#terms_open",
            )
            self.assertEqual(
                distribution.get("license"),
                "https://opendata.swiss/terms-of-use#terms_open",
            )
            self.assertEqual(distribution.get("issued"), self.dataset.get("issued"))
            self.assertEqual(distribution.get("modified"), self.dataset.get("modified"))
            self._is_multi_lang(distribution["title"])
            self._is_multi_lang(distribution["description"])

    def test_deprecated_WWW_DOWNLOAD_protocol_is_mapped_to_download_resource(self):
        deprecated_download_protocol = "WWW:DOWNLOAD-1.0-http--download"
        distribution = self._get_distribution_by_protocol(deprecated_download_protocol)
        self.assertIsNotNone(distribution)
        self.assertEqual(distribution.get("protocol"), deprecated_download_protocol)
        self.assertEqual(distribution.get("url"), distribution.get("download_url"))
        self.assertIsNotNone(distribution.get("media_type"))

    def test_deprecated_WMS_protocol(self):
        deprecated_wms_protocol = "OGC:WMS-http-get-capabilities"
        distribution = self._get_distribution_by_protocol(deprecated_wms_protocol)
        self.assertEqual(distribution.get("protocol"), deprecated_wms_protocol)
        self.assertIsNotNone(distribution)
        self.assertIsNone(distribution.get("download_url"))
        self.assertEqual(distribution.get("format"), "WMS")
        self.assertIsNone(distribution.get("media_type"))

    def test_deprecated_WMTS_protocol(self):
        deprecated_wmts_protocol = "OGC:WMTS-http-get-capabilities"
        distribution = self._get_distribution_by_protocol(deprecated_wmts_protocol)
        self.assertEqual(distribution.get("protocol"), deprecated_wmts_protocol)
        self.assertIsNotNone(distribution)
        self.assertIsNone(distribution.get("download_url"))
        self.assertEqual(distribution.get("format"), "WMTS")
        self.assertIsNone(distribution.get("media_type"))

    def test_deprecated_download_url_protocol(self):
        deprecated_download_url_protocol = "WWW:DOWNLOAD-URL"
        distribution = self._get_distribution_by_protocol(
            deprecated_download_url_protocol
        )
        self.assertIsNotNone(distribution)
        self.assertEqual(distribution.get("protocol"), deprecated_download_url_protocol)
        self.assertEqual(distribution.get("url"), distribution.get("download_url"))


class TestGeocatNormedDistributionProtocols(TestGeocatDistributionProtocols):
    def setUp(self):
        csw_map = self._set_csw()
        xml = self._load_xml("geocat-testdata.xml")
        geocat_identifier = "3143e92b-51fa-40ab-bcc0-fa389807e879"
        self.dataset = csw_map.get_metadata(xml, geocat_identifier)
        self.distributions = self.dataset.get("resources")

    def test_fields_that_come_from_the_dataset(self):
        self.assertEqual(6, len(self.distributions))
        for distribution in self.distributions:
            self.assertEqual(
                distribution.get("rights"),
                "https://opendata.swiss/terms-of-use#terms_by",
            )
            self.assertEqual(
                distribution.get("license"),
                "https://opendata.swiss/terms-of-use#terms_by",
            )
            self.assertEqual(distribution.get("issued"), self.dataset.get("issued"))
            self.assertEqual(distribution.get("modified"), self.dataset.get("modified"))
            self._is_multi_lang(distribution["title"])
            self._is_multi_lang(distribution["description"])

    def test_normed_protocol_WWW_DOWNLOAD_APP(self):
        download_app_protocol = "WWW:DOWNLOAD-APP"
        distribution = self._get_distribution_by_protocol(download_app_protocol)
        self.assertIsNotNone(distribution.get("url"))
        self.assertIsNone(distribution.get("download_url"))
        self.assertEqual("SERVICE", distribution.get("format"))

    def test_normed_protocol_OGC_WMS_without_gmd_name(self):
        ogc_wms_protocol = "OGC:WMS"
        distribution = self._get_distribution_by_protocol(ogc_wms_protocol)
        self.assertIsNotNone(distribution)
        self.assertIsNotNone(distribution.get("url"))
        self.assertIsNone(distribution.get("download_url"))
        self.assertEqual("WMS", distribution.get("format"))
        self.assertEqual("", distribution["title"]["de"])
        self.assertEqual("", distribution["title"]["en"])
        self.assertEqual("", distribution["title"]["fr"])
        self.assertEqual("", distribution["title"]["it"])

    def test_normed_protocol_Map_Preview(self):
        map_preview_protocol = "MAP:Preview"
        distribution = self._get_distribution_by_protocol(map_preview_protocol)
        self.assertIsNotNone(distribution)
        self.assertEqual(distribution["protocol"], map_preview_protocol)
        for lang in LANGUAGES:
            self.assertTrue(distribution["title"][lang].startswith("Map (Preview)"))
        self.assertIsNotNone(distribution.get("url"))
        self.assertIsNone(distribution.get("download_url"))
        self.assertEqual("SERVICE", distribution.get("format"))
        self.assertEqual("Map (Preview) Kartenvorschau", distribution["title"]["de"])
        self.assertEqual("Map (Preview)", distribution["title"]["en"])
        self.assertEqual("Map (Preview)", distribution["title"]["fr"])
        self.assertEqual("Map (Preview)", distribution["title"]["it"])

    def test_normed_protocol_ESRI_REST(self):
        esri_rest_protocol = "ESRI:REST"
        distribution = self._get_distribution_by_protocol(esri_rest_protocol)
        self.assertIsNotNone(distribution)
        self.assertIsNotNone(distribution.get("url"))
        self.assertIsNone(distribution.get("download_url"))
        self.assertEqual("API", distribution.get("format"))
        self.assertEqual("RESTful API von geo.admin.ch", distribution["title"]["de"])
        self.assertEqual("", distribution["title"]["en"])
        self.assertEqual("", distribution["title"]["fr"])
        self.assertEqual("", distribution["title"]["it"])

    def test_normed_protocol_WWW_DOWNLOAD_with_format_INTERLIS(self):
        download_protocol_with_format = "WWW:DOWNLOAD:INTERLIS"
        distribution = self._get_distribution_by_protocol(download_protocol_with_format)
        self.assertIsNotNone(distribution)
        self.assertEqual(distribution.get("url"), distribution.get("download_url"))
        self.assertEqual("INTERLIS", distribution.get("media_type"))
