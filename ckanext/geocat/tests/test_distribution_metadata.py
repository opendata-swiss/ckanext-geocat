"""Tests for metadata """
from ckanext.geocat.utils import csw_mapping
from nose.tools import *  # noqa
import os
from datetime import datetime
import time
import unittest

__location__ = os.path.realpath(
    os.path.join(
        os.getcwd(),
        os.path.dirname(__file__)
    )
)


class TestGeocatDistributionMetadataDesprecatedProtocols(unittest.TestCase):
    def setUp(self):
        self.csw_map = csw_mapping.GeoMetadataMapping(
            organization_slug="swisstopo",
            geocat_perma_link="https://perma-link/",
            geocat_perma_label="some label",
            legal_basis_url="",
            default_rights="",
            valid_identifiers=['8454f7d9-e3f2-4cc7-be6d-a82196660ccd@swisstopo'],
        )
        self.geocat_identifier_deprecated_protocols = '93814e81-2466-4690-b54d-c1d958f1c3b8'
        self.geocat_identifier_normed_protocols = '3143e92b-51fa-40ab-bcc0-fa389807e879'

    def _load_xml(self, filename):
        path = os.path.join(__location__, 'fixtures', filename)
        with open(path) as xml:
            entry = xml.read()
        return entry

    def _is_multi_lang(self, value):
        for lang in ['de', 'fr', 'it', 'en']:
            self.assertIn(lang, value)

    def test_all_resources(self):
        xml = self._load_xml('complete.xml')
        dataset = self.csw_map.get_metadata(xml, self.geocat_identifier_deprecated_protocols)
        distributions = dataset.get('resources')
        self.assertEquals(4, len(distributions))

    def test_deprecated_protocol_for_OGC_WMS(self):
        print("in test test_download_resources_with_deprecated_protocol_OGC_WMS")
        xml = self._load_xml('complete.xml')
        dataset = self.csw_map.get_metadata(xml, self.geocat_identifier_deprecated_protocols)
        distributions = dataset.get('resources')
        distribution = _get_distribution_by_protocol(distributions, "OGC:WMS-http-get-capabilities")
        self._is_multi_lang(distribution.get('title'))
        self.assertEquals(distribution.get('format'), 'WMS')
        self.assertIsNone(distribution.get('download_url'))
        self.assertEquals(distribution.get('url'), 'http://wms.geo.admin.ch/?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetCapabilities&lang=de/1')
        self.assertEquals(distribution['description']['fr'], 'Service WMS de geo.admin.ch')
        self.assertEquals(distribution['description']['de'], 'WMS Dienst von geo.admin.ch')
        self.assertEquals(distribution['description']['en'], 'WMS Service from geo.admin.ch')
        self.assertEquals(distribution['description']['it'], 'Servizio WMS di geo.admin.ch')

    def test_deprecated_protocol_for_OGC_WMTS(self):
        print("in test test_download_resources_with_deprecated_protocol_OGC_WMTS")
        xml = self._load_xml('complete.xml')
        dataset = self.csw_map.get_metadata(xml, self.geocat_identifier_deprecated_protocols)
        distributions = dataset.get('resources')
        distribution = _get_distribution_by_protocol(distributions, "OGC:WMTS-http-get-capabilities")
        self._is_multi_lang(distribution.get('title'))
        self._is_multi_lang(distribution.get('description'))
        self.assertEquals(distribution.get('format'), 'WMTS')
        self.assertIsNone(distribution.get('download_url'))
        self.assertEquals(distribution.get('url'), 'http://wmts.geo.admin.ch/1')

    def test_deprecated_protocol_for_WWW_DOWNLOAD_all_fields(self):
        print("in test test_download_resources_with_deprecated_protocol_WWW_DOWNLOAD")
        xml = self._load_xml('complete.xml')
        dataset = self.csw_map.get_metadata(xml, self.geocat_identifier_deprecated_protocols)
        distributions = dataset.get('resources')
        distribution = _get_distribution_by_protocol(distributions, "WWW:DOWNLOAD-1.0-http--download")
        self._is_multi_lang(distribution.get('title'))
        self._is_multi_lang(distribution.get('description'))
        self.assertEquals('Link zum Datenbezug', distribution['description']['de'])
        self.assertEquals(u'Lien vers la distribution des donn\xe9es', distribution['description']['fr'])
        self.assertEquals('Link per le fonti dei dati', distribution['description']['it'])
        self.assertEquals('Link for download', distribution['description']['en'])
        self.assertEquals('Link zum Datenbezug', distribution['title']['de'])
        self.assertEquals(u'Lien vers la distribution des donn\xe9es', distribution['title']['fr'])
        self.assertEquals('Link per le fonti dei dati', distribution['title']['it'])
        self.assertEquals('Link for download', distribution['title']['en'])
        date_string = '2011-12-31' # revision date from XML
        d = datetime.strptime(date_string, '%Y-%m-%d')
        self.assertEquals(int(time.mktime(d.timetuple())), distribution['issued'])
        self.assertEquals(int(time.mktime(d.timetuple())), distribution['modified'])
        self.assertSetEqual({'de', 'fr', 'en', 'it'}, set(distribution.get('language')))
        self.assertEquals('http://www.bafu.admin.ch/umwelt/12877/15716/15721/index.html?lang=de', distribution.get('url'))
        self.assertEquals('http://www.bafu.admin.ch/umwelt/12877/15716/15721/index.html?lang=de', distribution.get('download_url'))
        self.assertEquals(distribution.get('url'), distribution.get('download_url'))
        self.assertEquals('NonCommercialAllowed-CommercialAllowed-ReferenceNotRequired', distribution.get('rights'))
        self.assertEquals('', distribution.get('media_type'))
        self.assertEquals('', distribution.get('format'))

    def test_normed_protocol_WWW_DOWNLOAD_INTERLIS(self):
        print("in test_format_mapping_for_download_resource_normed_protocol")
        xml = self._load_xml('geocat_testdata.xml')
        dataset = self.csw_map.get_metadata(xml, self.geocat_identifier_normed_protocols)
        distributions = dataset.get('resources')
        distribution = _get_distribution_by_protocol(distributions, "WWW:DOWNLOAD:INTERLIS")
        self.assertEquals('https://data.geo.admin.ch', distribution.get('url'))
        self.assertEquals('https://data.geo.admin.ch', distribution.get('download_url'))
        self.assertEquals(distribution.get('url'), distribution.get('download_url'))
        self.assertEquals('NonCommercialAllowed-CommercialAllowed-ReferenceNotRequired', distribution.get('rights'))
        self.assertEquals('INTERLIS', distribution.get('media_type'))
        self.assertEquals('INTERLIS', distribution.get('format'))

    def test_normed_protocol_WWW_DOWNLOAD_APP(self):
        print("in test_format_mapping_for_download_resource_normed_protocol")
        xml = self._load_xml('geocat_testdata.xml')
        dataset = self.csw_map.get_metadata(xml, self.geocat_identifier_normed_protocols)
        distributions = dataset.get('resources')
        distribution = _get_distribution_by_protocol(distributions, "WWW:DOWNLOAD-APP")
        self.assertEquals('https://geocat.geoshop.ch', distribution.get('url'))
        self.assertIsNone(distribution.get('download_url'))

    def test_normed_protocol_Map_Preview(self):
        print("in test_format_mapping_for_download_resource_normed_protocol")
        xml = self._load_xml('geocat_testdata.xml')
        dataset = self.csw_map.get_metadata(xml, self.geocat_identifier_normed_protocols)
        distributions = dataset.get('resources')
        distribution = _get_distribution_by_protocol(distributions, "WWW:DOWNLOAD-APP")
        self.assertEquals('https://geocat.geoshop.ch', distribution.get('url'))
        self.assertIsNone(distribution.get('download_url'))


def _get_distribution_by_protocol(distributions, protocol):
    for distribution in distributions:
        print("-----------------------------------------")
        print("search protocol = {}".format(protocol))
        print("distribution protocol = {}".format(distribution.get('protocol')))
        print("distribution description = {}".format(distribution.get('description')))
        print("++++++++++++++++++++++++++++++++++++++++++++++++")
        if distribution.get('protocol') == protocol:
            print("return distribution")
            print(distribution)
            print("-===========================================")
            return distribution
