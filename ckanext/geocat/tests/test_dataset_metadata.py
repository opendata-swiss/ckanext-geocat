"""Tests for metadata """
from ckanext.geocat.utils import csw_mapping
from nose.tools import *  # noqa
import os
import json
from datetime import datetime
import time
import unittest
from pprint import pprint

__location__ = os.path.realpath(
    os.path.join(
        os.getcwd(),
        os.path.dirname(__file__)
    )
)


class TestGeocatDcatDatasetMetadata(unittest.TestCase):
    def setUp(self):
        self.csw_map = csw_mapping.GeoMetadataMapping(
            organization_slug="swisstopo",
            geocat_perma_link="https://perma-link/",
            geocat_perma_label="some label",
            legal_basis_url="",
            default_rights="",
            valid_identifiers=['8454f7d9-e3f2-4cc7-be6d-a82196660ccd@swisstopo'],
        )
        self.geocat_identifier = '93814e81-2466-4690-b54d-c1d958f1c3b8'

    def _load_xml(self, filename):
        path = os.path.join(__location__, 'fixtures', filename)
        with open(path) as xml:
            entry = xml.read()
        return entry

    def _is_multi_lang(self, value):
        for lang in ['de', 'fr', 'it', 'en']:
            self.assertIn(lang, value)

    def test_fields(self):
        xml = self._load_xml('testdata-deprecated-protocols.xml')
        dataset = self.csw_map.get_metadata(xml, self.geocat_identifier)

        fields = [
            'identifier',
            'title',
            'description',
            'issued',
            'modified',
            'publisher',
            'contact_points',
            'groups',
            'language',
            'relations',
            'temporals',
            'keywords',
            'url',
            'spatial',
            'coverage',
            'accrual_periodicity',
            'see_alsos',
            'owner_org',
            'resources'
        ]

        for field in fields:
            self.assertIn(field, dataset)

        # make sure only the defined fields are on the dataset
        self.assertEquals(sorted(fields), sorted(dataset.keys()))

        for key, value in dataset.iteritems():
            pprint(value)
            self.assertIn(key, fields)

        # check multilang fields
        self._is_multi_lang(dataset.get('title'))
        self._is_multi_lang(dataset.get('description'))

    def test_fields_values(self):
        xml = self._load_xml('testdata-deprecated-protocols.xml')
        dataset = self.csw_map.get_metadata(xml, self.geocat_identifier)

        # identifier
        self.assertEquals('93814e81-2466-4690-b54d-c1d958f1c3b8@swisstopo', dataset.get('identifier'))

        # title
        self.assertEquals(u'L\xe4rmbelastung durch Eisenbahnverkehr Nacht', dataset['title']['de'])
        self.assertEquals('Exposition au bruit du trafic ferroviaire, nuit', dataset['title']['fr'])
        self.assertEquals('Esposizione al rumore del traffico ferroviario, notte', dataset['title']['it'])
        self.assertEquals('Nighttime railway noise exposure', dataset['title']['en'])

        # description
        self.assertIn(u'Die Karte zeigt, welcher L\xe4rmbelastung', dataset['description']['de'])
        self.assertIn('', dataset['description']['fr'])
        self.assertIn('', dataset['description']['it'])
        self.assertIn('', dataset['description']['en'])

        # dates
        issued_modified_date = '2011-12-31T00:00:00'
        self.assertEquals(issued_modified_date, dataset['issued'])
        self.assertEquals(issued_modified_date, dataset['modified'])

        # publisher
        publisher = json.loads(dataset['publisher'])
        self.assertTrue(isinstance(publisher, dict))
        self.assertEquals(u'Bundesamt f\xfcr Umwelt', publisher['name'])
        self.assertEquals(u'http://www.bafu.admin.ch/abteilung-laerm-nis', publisher['url'])

        # contact points
        self.assertTrue(hasattr(dataset['contact_points'], '__iter__'))
        self.assertEquals(1, len(dataset['contact_points']))
        for contact_point in dataset['contact_points']:
            self.assertEquals('noise@bafu.admin.ch', contact_point['name'])
            self.assertEquals('noise@bafu.admin.ch', contact_point['email'])

        # groups
        groups = ['territory', 'geography']
        for group in dataset.get('groups'):
            self.assertIn(group['name'], groups)

        # language
        self.assertEquals(set(['de', 'fr', 'it', 'en']), set(dataset.get('language')))

        # relations
        self.assertTrue(hasattr(dataset['relations'], '__iter__'))
        self.assertEquals(2, len(dataset['relations']))
        for relation in dataset['relations']:
            self.assertIsNotNone(relation['label'])
            self.assertIsNotNone(relation['url'])

        # resources
        self.assertTrue(hasattr(dataset['resources'], '__iter__'))
        self.assertEquals(4, len(dataset['resources']))
        for relation in dataset['resources']:
            self.assertIsNotNone(relation['title'])
            self.assertIsNotNone(relation['description'])
            # Node with protocol OPENDATA:SWISS should not be mapped
            self.assertNotEquals(
                relation['description'], 'Permalink to dataset on opendata.swiss')
            self.assertIsNotNone(relation['url'])

        # temporals
        self.assertTrue(hasattr(dataset['temporals'], '__iter__'))
        self.assertEquals(0, len(dataset['temporals']))

        # keywords
        keywords = {
            'de': [
                'larmbekampfung',
                'larmbelastung',
                'larmpegel',
                'larmimmission',
                'verkehrslarm',
                'larmwirkung',
                'gesundheit-und-sicherheit',
                'e-geoch-geoportal'
            ],
            'fr': [
                'impact-du-bruit',
                'effet-du-bruit',
                'diminution-du-bruit',
                'niveau-sonore',
                'polluant-sonore',
                'sante-et-securite-des-personnes',
                'geoportail-e-geoch',
                'bruit-routier',
            ],
            'it': [
                'livello-del-rumore',
                'inquinante-acustico',
                'rumore-del-traffico',
                'effetto-del-rumore',
                'geoportale-e-geoch',
                'abbattimento-del-rumore',
                'salute-umana-e-sicurezza',
                'immissione-di-rumore',
            ],
            'en': [
                'noise-pollutant',
                'noise-level',
                'noise-abatement',
                'noise-immission',
                'human-health-and-safety',
                'traffic-noise',
                'noise-effect',
                'e-geoch-geoportal',
            ],
        }
        for lang in ['de', 'fr', 'it', 'en']:
            self.assertEquals(set(keywords[lang]), set(dataset['keywords'][lang]))

        # url
        self.assertEquals('http://www.bafu.admin.ch/laerm/', dataset.get('url'))

        # spatial
        self.assertEquals('Schweiz', dataset.get('spatial'))

        # coverage
        self.assertEquals('', dataset.get('coverage'))

        # accrual periodicity
        self.assertEquals('', dataset.get('accrual_periodicity'))

        # see alsos
        self.assertTrue(hasattr(dataset['see_alsos'], '__iter__'))
        self.assertEquals(1, len(dataset['see_alsos']))
        self.assertEquals('8454f7d9-e3f2-4cc7-be6d-a82196660ccd@swisstopo', dataset['see_alsos'][0])  # noqa

    def test_fields_values_de_only(self):
        xml = self._load_xml('only_de.xml')
        dataset = self.csw_map.get_metadata(xml, self.geocat_identifier)

        # identifier
        self.assertEquals('93814e81-2466-4690-b54d-c1d958f1c3b8@swisstopo', dataset.get('identifier'))

        # title
        self.assertEquals(u'L\xe4rmbelastung durch Eisenbahnverkehr Nacht', dataset['title']['de'])
        self.assertEquals('', dataset['title']['fr'])
        self.assertEquals('', dataset['title']['it'])
        self.assertEquals('', dataset['title']['en'])

        # description
        self.assertIn(u'Die Karte zeigt, welcher L\xe4rmbelastung', dataset['description']['de'])
        self.assertIn('', dataset['description']['fr'])
        self.assertIn('', dataset['description']['it'])
        self.assertIn('', dataset['description']['en'])

        # language
        self.assertEquals(set(['de']), set(dataset.get('language')))

        # keywords
        keywords = {
            'de': [
                'larmbekampfung',
                'larmbelastung',
                'larmpegel',
                'larmimmission',
                'verkehrslarm',
                'larmwirkung',
                'gesundheit-und-sicherheit',
                'e-geoch-geoportal'
            ],
            'fr': [],
            'it': [],
            'en': [],
        }
        for lang in ['de', 'fr', 'it', 'en']:
            self.assertEquals(set(keywords[lang]), set(dataset['keywords'][lang]))

    def test_date_revision(self):
        xml = self._load_xml('revision_date.xml')
        dataset = self.csw_map.get_metadata(xml, self.geocat_identifier)

        revision_date = '2011-12-31T00:00:00'
        self.assertEquals(revision_date, dataset['issued'])
        self.assertEquals(revision_date, dataset['modified'])

    def test_date_publication(self):
        xml = self._load_xml('publication_date.xml')
        dataset = self.csw_map.get_metadata(xml, self.geocat_identifier)

        self.assertEquals('2010-12-30T00:00:00', dataset['issued'])
        self.assertEquals('2011-12-31T00:00:00', dataset['modified'])

        self.assertNotEquals(dataset['issued'], dataset['modified'])

    def test_date_issued_before_1900(self):
        xml = self._load_xml('publication_date_before_1900.xml')
        dataset = self.csw_map.get_metadata(xml, self.geocat_identifier)

        self.assertEquals(dataset['issued'], '1891-12-30T00:00:00')
        self.assertEquals(dataset['modified'], '1891-12-31T00:00:00')

    def test_documentation(self):
        xml = self._load_xml('geocat-testdata.xml')
        dataset = self.csw_map.get_metadata(xml, self.geocat_identifier)

        self.assertEquals(
            sorted(dataset['documentation']),
            [
                "https://example.org/documentation/1",
                "https://example.org/documentation/2"
            ]
        )


if __name__ == '__main__':
    unittest.main()
