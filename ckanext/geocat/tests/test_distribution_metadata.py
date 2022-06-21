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


class TestGeocatDistributionProtocols(unittest.TestCase):
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

    def test_deprecated_protocol_for_WWW_DOWNLOAD(self):
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

    def test_normed_protocol_WWW_DOWNLOAD_INTERLIS(self):
        xml = self._load_xml('geocat-testdata.xml')
        dataset = self.csw_map.get_metadata(xml, self.geocat_identifier_normed_protocols)
        distributions = dataset.get('resources')
        distribution = _get_distribution_by_protocol(distributions, "WWW:DOWNLOAD:INTERLIS")
        self.assertEquals('https://data.geo.admin.ch', distribution.get('url'))
        self.assertEquals('https://data.geo.admin.ch', distribution.get('download_url'))
        self.assertEquals(distribution.get('url'), distribution.get('download_url'))
        self.assertEquals('NonCommercialAllowed-CommercialAllowed-ReferenceRequired', distribution.get('rights'))
        self.assertEquals('INTERLIS', distribution.get('media_type'))

    def test_normed_protocol_WWW_DOWNLOAD_APP(self):
        xml = self._load_xml('geocat-testdata.xml')
        dataset = self.csw_map.get_metadata(xml, self.geocat_identifier_normed_protocols)
        distributions = dataset.get('resources')
        distribution = _get_distribution_by_protocol(distributions, "WWW:DOWNLOAD-APP")
        self.assertEquals('https://geocat.geoshop.ch', distribution.get('url'))
        self.assertIsNone(distribution.get('download_url'))

    def test_normed_protocol_Map_Preview(self):
        xml = self._load_xml('geocat-testdata.xml')
        dataset = self.csw_map.get_metadata(xml, self.geocat_identifier_normed_protocols)
        distributions = dataset.get('resources')
        distribution = _get_distribution_by_protocol(distributions, "MAP:Preview")
        self.assertEquals('https://map.geo.admin.ch/?layers=ch.bfe.energiestaedte', distribution.get('url'))
        self.assertIsNone(distribution.get('download_url'))

    def test_normed_protocol_OGC_WMS(self):
        xml = self._load_xml('geocat-testdata.xml')
        dataset = self.csw_map.get_metadata(xml, self.geocat_identifier_normed_protocols)
        distributions = dataset.get('resources')
        distribution = _get_distribution_by_protocol(distributions, "OGC:WMS")
        self.assertEquals(distribution.get('format'), 'WMS')
        self.assertIsNone(distribution.get('download_url'))
        self.assertEquals('http://wms.geo.admin.ch/?SERVICE', distribution.get('url'))
        self.assertIsNone(distribution.get('download_url'))


def _get_distribution_by_protocol(distributions, protocol):
    for distribution in distributions:
        if distribution.get('protocol') == protocol:
            return distribution
