"""Tests for metadata"""

import os
import unittest

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
