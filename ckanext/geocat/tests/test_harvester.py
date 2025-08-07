import json
import logging
import os
from pprint import pprint

import ckan.plugins.toolkit as tk
import ckantoolkit.tests.helpers as h
import pytest
import requests_mock
from ckan import model
from ckan.common import config

from ckanext.geocat.harvester import GeocatHarvester
from ckanext.harvest import queue
from ckanext.harvest.tests import factories as harvest_factories
from ckanext.harvest.tests.lib import run_harvest

log = logging.getLogger(__name__)

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))

MOCK_URL = "http://mock-geocat.ch"
mock_record_url = "http://mock-geocat.ch/geonetwork/srv/eng/csw-BAKOM"
mock_capabilities_url = (
    "http://mock-geocat.ch/?version=2.0.2&request=GetCapabilities&service=CSW"
)


@pytest.mark.ckan_config(
    "ckan.plugins",
    "ogdch ogdch_pkg harvest ckan_harvester geocat_harvester scheming_datasets fluent",
)
@pytest.mark.usefixtures("with_plugins", "clean_db", "clean_index")
class TestGeocatHarvestFunctional:
    def _run_jobs(self, harvest_source_id=None):
        try:
            h.call_action("harvest_jobs_run", {}, source_id=harvest_source_id)
        except Exception as e:
            if str(e) == "There are no new harvesting jobs":
                pass

    def _test_harvest_create(
        self,
        all_results_filename,
        single_results_filenames,
        num_objects,
        expected_packages,
        mocker,
        harvest_source,
        **kwargs,
    ):
        self._mock_csw_results(all_results_filename, single_results_filenames, mocker)

        results_by_guid = run_harvest(MOCK_URL, GeocatHarvester())
        assert len(results_by_guid) == expected_packages

        # Check that correct amount of datasets were created
        fq = "+type:dataset harvest_source_id:{0}".format(harvest_source["id"])
        results = h.call_action("package_search", {}, fq=fq)
        assert results["count"] == expected_packages

        return results

    def _mock_csw_results(self, all_results_filename, single_results_filenames, mocker):
        path = os.path.join(
            __location__, "fixtures", "test_harvesters", all_results_filename
        )
        with open(path) as xml:
            all_results = xml.read()

        mocker.post(mock_record_url, text=all_results)

        responses = []
        for filename in single_results_filenames:
            path = os.path.join(__location__, "fixtures", "test_harvesters", filename)
            with open(path) as xml:
                result = xml.read()

            responses.append({"text": result})

        mocker.get(mock_record_url, responses)
        print(mock_record_url)

    def test_harvest_create_simple(
        self, ogdch_requests_mock, user, org, harvest_source
    ):
        self._test_harvest_create(
            "response_all_results.xml",
            [
                "result_1.xml",
                "result_2.xml",
            ],
            num_objects=2,
            expected_packages=2,
            mocker=ogdch_requests_mock,
            harvest_source=harvest_source,
        )

    def test_harvest_deleted_dataset(self):
        test_config_deleted = json.dumps({"delete_missing_datasets": True})

        # Import two datasets
        results = self._test_harvest_create(
            "response_all_results.xml",
            [
                "result_1.xml",
                "result_2.xml",
            ],
            2,
            2,
            config=test_config_deleted,
        )

        # Run jobs to mark the old job finished
        self._run_jobs()

        # Import again, this time with only one dataset
        results = self._test_harvest_create(
            "response_just_one_result.xml",
            ["result_1.xml"],
            2,
            1,
            config=test_config_deleted,
        )
        assert (
            results["results"][0]["name"]
            == "larmbelastung-durch-eisenbahnverkehr-nacht"
        )

        self._run_jobs()

        # Get the harvest source with the updated status
        harvest_source = self._get_or_create_harvest_source(config=test_config_deleted)

        last_job_status = harvest_source["status"]["last_job"]
        assert last_job_status["status"] == "Finished"

        error_count = len(last_job_status["object_error_summary"])
        assert error_count == 0
