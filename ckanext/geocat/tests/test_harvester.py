import json
import logging
import os

import ckan.plugins.toolkit as tk
import ckantoolkit.tests.helpers as h
import pytest
import requests
import requests_mock
from ckan import model
from ckan.common import config

from ckanext.harvest import queue

log = logging.getLogger(__name__)

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))

MOCK_URL = "http://mock-geocat.ch"
mock_record_url = "http://mock-geocat.ch/geonetwork/srv/eng/csw-BAKOM"
mock_capabilities_url = (
    "http://mock-geocat.ch/?version=2.0.2&request=GetCapabilities&service=CSW"
)
clear_solr_url = (
    config.get("solr_url")
    + "/update?stream.body=%3Cdelete%3E%3Cquery%3Ename:geocat-harvester%20OR%20organization:geocat_org%3C/query%3E%3C/delete%3E&commit=true"
)


@pytest.mark.ckan_config(
    "ckan.plugins",
    "ogdch ogdch_pkg harvest ckan_harvester geocat_harvester scheming_datasets fluent",
)
@pytest.mark.usefixtures("with_plugins", "clean_db", "clean_index")
class TestGeocatHarvestFunctional:
    @classmethod
    @pytest.fixture(autouse=True, scope="class")
    def setup_class(cls):
        h.reset_db()

        cls.gather_consumer = queue.get_gather_consumer()
        cls.fetch_consumer = queue.get_fetch_consumer()

    @pytest.fixture(autouse=True)
    def setup(self):
        queue.purge_queues()
        requests.get(clear_solr_url)

        self.user_dict = h.call_action(
            "user_create",
            name="test_admin",
            email="testuser@example.com",
            password="password",
        )
        user_obj = model.User.get(self.user_dict["name"])
        user_obj.sysadmin = True
        model.Session.add(user_obj)
        model.Session.commit()

        org_name = "test-org"
        org_data_dict = {"name": org_name}

        org_context = {
            "model": model,
            "session": model.Session,
            "user": self.user_dict["name"],
        }
        org = tk.get_action("organization_create")(org_context, org_data_dict)
        self.org_id = org["id"]

        yield

        h.reset_db()
        queue.purge_queues()
        requests.get(clear_solr_url)

    @pytest.fixture(autouse=True)
    def _get_or_create_harvest_source(self, setup, **kwargs):
        source_dict = {
            "title": "Geocat harvester",
            "name": "geocat-harvester",
            "url": MOCK_URL,
            "source_type": "geocat_harvester",
            "owner_org": self.org_id,
        }
        context = {
            "model": model,
            "session": model.Session,
            "user": self.user_dict["name"],
            "ignore_auth": True,
        }
        source_dict.update(**kwargs)

        try:
            harvest_source = tk.get_action("harvest_source_show", {}, source_dict)
        except Exception as e:
            harvest_source = tk.get_action("harvest_source_create")(
                context, source_dict
            )

        return harvest_source

    def _create_harvest_job(self, harvest_source_id):
        harvest_job = h.call_action(
            "harvest_job_create", {}, source_id=harvest_source_id
        )

        return harvest_job

    def _run_jobs(self, harvest_source_id=None):
        try:
            h.call_action("harvest_jobs_run", {}, source_id=harvest_source_id)
        except Exception as e:
            if str(e) == "There are no new harvesting jobs":
                pass

    def _gather_queue(self, num_jobs=1):
        for job in range(num_jobs):
            # Pop one item off the queue (the job id) and run the callback
            reply = self.gather_consumer.basic_get(queue="ckan.harvest.gather.test")

            # Make sure something was sent to the gather queue
            assert reply[2], "Empty gather queue"

            # Send the item to the gather callback, which will call the
            # harvester gather_stage
            queue.gather_callback(self.gather_consumer, *reply)

    def _fetch_queue(self, num_objects=1):
        for _object in range(num_objects):
            # Pop item from the fetch queues (object ids) and run the callback,
            # one for each object created
            reply = self.fetch_consumer.basic_get(queue="ckan.harvest.fetch.test")

            # Make sure something was sent to the fetch queue
            assert reply[2], "Empty fetch queue, the gather stage failed"

            # Send the item to the fetch callback, which will call the
            # harvester fetch_stage and import_stage
            queue.fetch_callback(self.fetch_consumer, *reply)

    def _run_full_job(self, harvest_source_id, num_jobs=1, num_objects=1):
        # Create new job for the source
        self._create_harvest_job(harvest_source_id)

        # Run the job
        self._run_jobs(harvest_source_id)

        # Handle the gather queue
        self._gather_queue(num_jobs)

        # Handle the fetch queue
        self._fetch_queue(num_objects)

    @requests_mock.Mocker(real_http=True)
    def _test_harvest_create(
        self,
        all_results_filename,
        single_results_filenames,
        num_objects,
        expected_packages,
        mocker,
        **kwargs
    ):
        self._mock_csw_results(all_results_filename, single_results_filenames, mocker)

        harvest_source = self._get_or_create_harvest_source(**kwargs)

        self._run_full_job(harvest_source["id"], num_objects=num_objects)

        # Check that correct amount of datasets were created
        fq = "+type:dataset harvest_source_id:{0}".format(harvest_source["id"])
        results = h.call_action("package_search", {}, fq=fq)
        assert results["count"] == expected_packages

        return results

    def _mock_csw_results(self, all_results_filename, single_results_filenames, mocker):
        path = os.path.join(
            __location__, "fixtures", "test_harvesters", "capabilities.xml"
        )
        with open(path) as xml:
            capabilities = xml.read()

        mocker.get(mock_capabilities_url, text=capabilities)

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

    def test_harvest_create_simple(self):
        self._test_harvest_create(
            "response_all_results.xml",
            [
                "result_1.xml",
                "result_2.xml",
            ],
            num_objects=2,
            expected_packages=2,
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
