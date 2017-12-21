"""Tests for harvester """
from nose.tools import assert_equal, assert_raises, assert_in
import httpretty

import GeocatHarvester from ckanext.geocat.harvester

from ckan.tests.helpers import reset_db, call_action

from ckan import model
from ckan.plugins import toolkit

from ckanext.harvest.tests.factories import (HarvestSourceObj, HarvestJobObj,
                                             HarvestObjectObj)
from ckanext.harvest.tests.lib import run_harvest

class TestGeocatHarvester(object):
    @classmethod
    def setup(cls):
        reset_db()
        harvest_model.setup()

    def test_harvest(self):

        httpretty.register_uri(httpretty.GET, url,
                               body=content, content_type=content_type)

        results = run_harvest(
            url='http://my-test-geocat.test/csw' 
            harvester=GeocatHarvester())

        result = results['dataset1-id']
        assert_equal(result['state'], 'COMPLETE')
        assert_equal(result['report_status'], 'added')
        assert_equal(result['dataset']['name'], 'Test')
        assert_equal(result['errors'], [])

