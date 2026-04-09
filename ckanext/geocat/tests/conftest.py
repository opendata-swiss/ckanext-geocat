import json
import os.path

import pytest
from ckan.tests import factories

from ckanext.harvest.tests import factories as harvest_factories

location = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
mock_capabilities_url = (
    "http://mock-geocat.ch/?version=2.0.2&request=GetCapabilities&service=CSW"
)


@pytest.fixture
def ogdch_requests_mock(requests_mock):
    requests_mock.real_http = True

    # Mock capabilities response (this is always the same)
    path = os.path.join(location, "fixtures", "test_harvesters", "capabilities.xml")
    with open(path) as xml:
        capabilities = xml.read()
    requests_mock.get(mock_capabilities_url, text=capabilities)

    return requests_mock


@pytest.fixture
def clean_db(reset_db, migrate_db_for):
    reset_db()
    migrate_db_for("harvest")


@pytest.fixture
def org():
    return factories.Organization(name="test-org")


@pytest.fixture
def harvest_source(org):
    """Create a harvest source with the required url. We don't call it explicitly in the
    tests, but this means that when we call ckanext.harvest.tests.lib.run_harvest and
    specify the same url, the harvest source we create here will be used every time.
    """
    return harvest_factories.HarvestSource(
        title="Geocat harvester",
        name="geocat-harvester",
        url="http://mock-geocat.ch",
        source_type="geocat_harvester",
        owner_org=org["id"],
        config=json.dumps({"delete_missing_datasets": True}),
    )


@pytest.fixture
def harvest_source_ech0271(org):
    """Harvest source for DCAT-AP-CH / eCH-0271 (``geocat-ech0271``) functional tests."""
    return harvest_factories.HarvestSource(
        title="Geocat eCH-0271 harvester",
        name="geocat-ech0271-harvester",
        url="http://mock-geocat.ch",
        source_type="geocat-ech0271",
        owner_org=org["id"],
        config=json.dumps({"delete_missing_datasets": True}),
    )
