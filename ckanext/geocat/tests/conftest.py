import logging
import pytest
import requests
import ckantoolkit.tests.helpers as h

import ckanext.harvest.model as harvest_model
from ckanext.harvest import queue
from ckan.common import config

log = logging.getLogger(__name__)

mock_url = "http://mock-geocat.ch"
solr_url = config.get("solr_url", "http://localhost:8983/solr/ckan")
clear_solr_url = (
    solr_url
    + "/update?stream.body=%3Cdelete%3E%3Cquery%3Ename:geocat-harvester%20OR%20organization:geocat_org%3C/query%3E%3C/delete%3E&commit=true"
)


@pytest.fixture(scope="session")
def gather_consumer():
    return queue.get_gather_consumer()


@pytest.fixture(scope="session")
def fetch_consumer():
    return queue.get_fetch_consumer()


@pytest.fixture
def harvest_env():
    h.reset_db()
    queue.purge_queues()
    # Optional: avoid Solr dependency for isolated tests
    try:
	    requests.get(clear_solr_url, timeout=2)
    except requests.ConnectionError:
	    print("Solr not available on localhost:8983 — skipping Solr clearing.")
    yield
    h.reset_db()
    queue.purge_queues()
    requests.get(clear_solr_url)


@pytest.fixture
def test_user_and_org():
    user = h.call_action(
        "user_create",
        name="testuser",
        email="testuser@example.com",
        password="password",
    )
    org_context = {"user": user["name"], "return_id_only": True}
    org_data = {"name": "geocat_org"}
    org_id = h.call_action("organization_create", org_context, **org_data)
    return user["name"], org_id
