import logging
import os
import re

import ckan.plugins.toolkit as tk
import pytest

from ckanext.geocat.harvester import GeocatEch0271Harvester
from ckanext.harvest.tests.lib import run_harvest

log = logging.getLogger(__name__)

# Canonical DCAT-AP-CH per-record XML: result_1_dcat.xml, result_2_dcat.xml (OCurdy branch).
# response_getrecords_dcat_*.xml is assembled from those; after edits run:
#   python3 bin/regen_dcat_harvest_fixtures.py
__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))

MOCK_URL = "http://mock-geocat.ch"


def _mock_getrecords_dcat(mocker, xml_filename):
    path = os.path.join(__location__, "fixtures", "test_harvesters", xml_filename)
    with open(path) as xml:
        body = xml.read()

    def _is_getrecords(request):
        return "GETRECORDS" in request.url.upper()

    mocker.get(
        re.compile(r"^http://mock-geocat\.ch"),
        text=body,
        additional_matcher=_is_getrecords,
    )


def _test_harvest_create_ech0271(
    batch_xml_filename,
    expected_packages,
    mocker,
    harvest_source_ech0271,
):
    _mock_getrecords_dcat(mocker, batch_xml_filename)

    results_by_guid = run_harvest(MOCK_URL, GeocatEch0271Harvester())

    for harvest_object_result in results_by_guid.values():
        assert harvest_object_result["state"] == "COMPLETE"
        assert len(harvest_object_result["errors"]) == 0

    fq = "+type:dataset harvest_source_id:{0}".format(harvest_source_ech0271["id"])
    results = tk.get_action("package_search")({}, {"fq": fq})
    assert results["count"] == expected_packages

    return results


@pytest.mark.ckan_config(
    "ckan.plugins",
    "ogdch ogdch_pkg harvest ckan_harvester geocat_harvester "
    "geocat_ech0271_harvester scheming_datasets fluent",
)
@pytest.mark.usefixtures("with_plugins", "clean_db", "clean_index", "clean_queues")
class TestGeocatEch0271HarvestFunctional:
    def test_harvest_create_simple(self, ogdch_requests_mock, harvest_source_ech0271):
        _test_harvest_create_ech0271(
            "response_getrecords_dcat_batch.xml",
            expected_packages=2,
            mocker=ogdch_requests_mock,
            harvest_source_ech0271=harvest_source_ech0271,
        )

    def test_harvest_deleted_dataset(self, ogdch_requests_mock, harvest_source_ech0271):
        _test_harvest_create_ech0271(
            "response_getrecords_dcat_batch.xml",
            expected_packages=2,
            mocker=ogdch_requests_mock,
            harvest_source_ech0271=harvest_source_ech0271,
        )

        results = _test_harvest_create_ech0271(
            "response_getrecords_dcat_one.xml",
            expected_packages=1,
            mocker=ogdch_requests_mock,
            harvest_source_ech0271=harvest_source_ech0271,
        )
        assert (
            results["results"][0]["name"]
            == "larmbelastung-durch-eisenbahnverkehr-nacht"
        )
