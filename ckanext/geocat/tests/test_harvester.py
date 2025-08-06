import json
import logging
import os

import ckantoolkit.tests.helpers as helpers
import pytest
import requests
import requests_mock
from ckan.common import config

import ckanext.harvest.model as harvest_model
from ckanext.harvest import queue

log = logging.getLogger(__name__)

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))

mock_url = "http://mock-geocat.ch"
mock_record_url = "http://mock-geocat.ch/geonetwork/srv/eng/csw-BAKOM"
mock_capabilities_url = (
    "http://mock-geocat.ch/?version=2.0.2&request=GetCapabilities&service=CSW"
)
clear_solr_url = (
    config.get("solr_url")
    + "/update?stream.body=%3Cdelete%3E%3Cquery%3Ename:geocat-harvester%20OR%20organization:geocat_org%3C/query%3E%3C/delete%3E&commit=true"
)


@pytest.fixture(scope="class")
def gather_fetch_consumers():
    helpers.reset_db()
    yield {"gather": queue.get_gather_consumer(), "fetch": queue.get_fetch_consumer()}
    helpers.reset_db()
    queue.purge_queues()
    requests.get(clear_solr_url)


@pytest.fixture
def org():
    user_dict = helpers.call_action(
        "user_create",
        name="testuser",
        email="testuser@example.com",
        password="password",
    )
    context = {"user": user_dict["name"], "return_id_only": True}
    org_dict = {"name": "geocat_org"}
    return helpers.call_action("organization_create", context, **org_dict)


@pytest.fixture(autouse=True)
def clean_environment():
    harvest_model.setup()
    queue.purge_queues()
    requests.get(clear_solr_url)
    yield
    helpers.reset_db()
    queue.purge_queues()
    requests.get(clear_solr_url)


def get_or_create_harvest_source(org_id, **kwargs):
    source_dict = {
        "title": "Geocat harvester",
        "name": "geocat-harvester",
        "url": mock_url,
        "source_type": "geocat_harvester",
        "owner_org": org_id,
    }
    source_dict.update(**kwargs)
    try:
        return helpers.call_action("harvest_source_show", {}, **source_dict)
    except Exception:
        return helpers.call_action("harvest_source_create", {}, **source_dict)


def create_harvest_job(source_id):
    return helpers.call_action("harvest_job_create", {}, source_id=source_id)


def run_jobs(source_id=None):
    try:
        helpers.call_action("harvest_jobs_run", {}, source_id=source_id)
    except Exception as e:
        if str(e) != "There are no new harvesting jobs":
            raise


def process_gather_queue(gather_consumer, num_jobs=1):
    for _ in range(num_jobs):
        reply = gather_consumer.basic_get(queue="ckan.harvest.gather.test")
        assert reply[2], "Empty gather queue"
        queue.gather_callback(gather_consumer, *reply)


def process_fetch_queue(fetch_consumer, num_objects=1):
    for _ in range(num_objects):
        reply = fetch_consumer.basic_get(queue="ckan.harvest.fetch.test")
        assert reply[2], "Empty fetch queue, the gather stage failed"
        queue.fetch_callback(fetch_consumer, *reply)


def run_full_job(source_id, gather_consumer, fetch_consumer, num_jobs=1, num_objects=1):
    create_harvest_job(source_id)
    run_jobs(source_id)
    process_gather_queue(gather_consumer, num_jobs)
    process_fetch_queue(fetch_consumer, num_objects)


def mock_csw_results(all_results_filename, single_results_filenames, mocker):
    cap_path = os.path.join(
        __location__, "fixtures", "test_harvesters", "capabilities.xml"
    )
    with open(cap_path) as xml:
        mocker.get(mock_capabilities_url, text=xml.read())

    all_path = os.path.join(
        __location__, "fixtures", "test_harvesters", all_results_filename
    )
    with open(all_path) as xml:
        mocker.post(mock_record_url, text=xml.read())

    responses = []
    for filename in single_results_filenames:
        path = os.path.join(__location__, "fixtures", "test_harvesters", filename)
        with open(path) as xml:
            responses.append({"text": xml.read()})
    mocker.get(mock_record_url, responses)

    @pytest.mark.usefixtures("clean_environment")
    class TestGeocatHarvestFunctional:
        @pytest.mark.parametrize(
            "all_results_filename,single_results_filenames,num_objects,expected_packages",
            [
                ("response_all_results.xml", ["result_1.xml", "result_2.xml"], 2, 2),
            ],
        )
        def test_harvest_create_simple(
            self,
            org,
            gather_fetch_consumers,
            requests_mock,
            all_results_filename,
            single_results_filenames,
            num_objects,
            expected_packages,
        ):
            mock_csw_results(
                all_results_filename, single_results_filenames, requests_mock
            )

            source = get_or_create_harvest_source(org)
            run_full_job(
                source["id"],
                gather_fetch_consumers["gather"],
                gather_fetch_consumers["fetch"],
                num_jobs=1,
                num_objects=num_objects,
            )

            fq = f"+type:dataset harvest_source_id:{source['id']}"
            results = helpers.call_action("package_search", {}, fq=fq)
            assert results["count"] == expected_packages

        def test_harvest_deleted_dataset(
            self, org, gather_fetch_consumers, requests_mock
        ):
            config_deleted = json.dumps({"delete_missing_datasets": True})

            # Import two datasets
            mock_csw_results(
                "response_all_results.xml",
                ["result_1.xml", "result_2.xml"],
                requests_mock,
            )
            source = get_or_create_harvest_source(org, config=config_deleted)
            run_full_job(
                source["id"],
                gather_fetch_consumers["gather"],
                gather_fetch_consumers["fetch"],
                num_objects=2,
            )

            # Mark old job as finished
            run_jobs()

            # Import again with only one result
            mock_csw_results(
                "response_just_one_result.xml", ["result_1.xml"], requests_mock
            )
            run_full_job(
                source["id"],
                gather_fetch_consumers["gather"],
                gather_fetch_consumers["fetch"],
                num_objects=2,
            )

            results = helpers.call_action(
                "package_search", {}, fq=f"harvest_source_id:{source['id']}"
            )
            assert (
                results["results"][0]["name"]
                == "larmbelastung-durch-eisenbahnverkehr-nacht"
            )

            run_jobs()

            updated_source = get_or_create_harvest_source(org, config=config_deleted)
            last_status = updated_source["status"]["last_job"]
            assert last_status["status"] == "Finished"
            assert len(last_status["object_error_summary"]) == 0
