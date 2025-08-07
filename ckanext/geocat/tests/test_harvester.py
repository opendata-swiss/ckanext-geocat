import logging
import os

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


def _mock_csw_results(all_results_filename, single_results_filenames, mocker):
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


def _test_harvest_create(
    all_results_filename,
    single_results_filenames,
    expected_packages,
    mocker,
    harvest_source,
):
    _mock_csw_results(all_results_filename, single_results_filenames, mocker)

    results_by_guid = run_harvest(MOCK_URL, GeocatHarvester())

    for harvest_object_result in results_by_guid.values():
        assert harvest_object_result["state"] == "COMPLETE"
        assert len(harvest_object_result["errors"]) == 0

    # Check that correct amount of datasets were created
    fq = "+type:dataset harvest_source_id:{0}".format(harvest_source["id"])
    results = h.call_action("package_search", {}, fq=fq)
    assert results["count"] == expected_packages

    return results


@pytest.mark.ckan_config(
    "ckan.plugins",
    "ogdch ogdch_pkg harvest ckan_harvester geocat_harvester scheming_datasets fluent",
)
@pytest.mark.usefixtures("with_plugins", "clean_db", "clean_index", "clean_queues")
class TestGeocatHarvestFunctional:
    def test_harvest_create_simple(
        self, ogdch_requests_mock, user, org, harvest_source
    ):
        _test_harvest_create(
            "response_all_results.xml",
            [
                "result_1.xml",
                "result_2.xml",
            ],
            expected_packages=2,
            mocker=ogdch_requests_mock,
            harvest_source=harvest_source,
        )

    def test_harvest_deleted_dataset(
        self, ogdch_requests_mock, user, org, harvest_source
    ):
        # Import two datasets
        _test_harvest_create(
            "response_all_results.xml",
            [
                "result_1.xml",
                "result_2.xml",
            ],
            expected_packages=2,
            mocker=ogdch_requests_mock,
            harvest_source=harvest_source,
        )

        # Import again, this time with only one dataset
        results = _test_harvest_create(
            "response_just_one_result.xml",
            ["result_1.xml"],
            expected_packages=1,
            mocker=ogdch_requests_mock,
            harvest_source=harvest_source,
        )
        assert (
            results["results"][0]["name"]
            == "larmbelastung-durch-eisenbahnverkehr-nacht"
        )
