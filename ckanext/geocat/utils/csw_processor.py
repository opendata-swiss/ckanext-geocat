import logging

import requests
from lxml import etree
from owslib.catalogue.csw2 import CatalogueServiceWeb
from owslib.fes import PropertyIsEqualTo

log = logging.getLogger(__name__)

CHE_SCHEMA = "http://www.geocat.ch/2008/che"
DCAT_AP_CH_SCHEMA = "http://dcat-ap.ch/schema/dcat-ap-ch/2.0"
CQL_QUERY_DEFAULT = "subject"
CQL_SEARCH_TERM_DEFAULT = "opendata.swiss"

_DCAT_DATASET_TAG = "{http://www.w3.org/ns/dcat#}Dataset"
_DCT_IDENTIFIER_TAG = "{http://purl.org/dc/terms/}identifier"

# Wraps a single dcat:Dataset in a minimal GetRecordByIdResponse envelope
# so that dcat_mapping.DcatMetadataMapping can parse it unchanged.
_GETRECORDBYID_ENVELOPE = (
    '<?xml version="1.0" encoding="UTF-8"?>'
    '<csw:GetRecordByIdResponse xmlns:csw="http://www.opengis.net/cat/csw/2.0.2">'
    "{dataset_xml}"
    "</csw:GetRecordByIdResponse>"
)

_CSW_SEARCH_RESULTS_NS = {"csw": "http://www.opengis.net/cat/csw/2.0.2"}


def _build_cql_params(cql, cql_query, cql_search_term):
    """Return the CQL constraint parameters to add to a GetRecords request."""
    if cql_query and cql_search_term:
        constraint = f"{cql_query} = '{cql_search_term}'"
    elif cql:
        constraint = cql
    else:
        constraint = f"{CQL_QUERY_DEFAULT} = '{CQL_SEARCH_TERM_DEFAULT}'"
    return {
        "CONSTRAINTLANGUAGE": "CQL_TEXT",
        "CONSTRAINT_LANGUAGE_VERSION": "1.1.0",
        "CONSTRAINT": constraint,
    }


def _next_record_from_results(root, current_start):
    """Return the next start position from a GetRecords response, or None if done."""
    csw_search_results = root.find(".//csw:SearchResults", _CSW_SEARCH_RESULTS_NS)
    if csw_search_results is None:
        return None
    next_record = int(csw_search_results.get("nextRecord", 0))
    matched = int(csw_search_results.get("numberOfRecordsMatched", 0))
    returned = int(csw_search_results.get("numberOfRecordsReturned", 0))
    log.debug(
        "GetRecords: matched=%s returned=%s nextRecord=%s start=%s",
        matched,
        returned,
        next_record,
        current_start,
    )
    if next_record == 0 or next_record > matched or returned == 0:
        return None
    if next_record <= current_start:
        log.warning(
            "Ignoring non-advancing nextRecord=%s (<= start=%s); end of results",
            next_record,
            current_start,
        )
        return None
    return next_record


class GeocatCatalogueServiceWeb(object):
    """
    CSW client for the classic ``geocat_harvester`` (ISO19139.che via OWSLib).

    Used by opendata-swiss production sources that expect CHE outputSchema and
    ``csw_mapping.GeoMetadataMapping``.
    """

    def __init__(self, url):
        self.csw = CatalogueServiceWeb(url)
        self.schema = CHE_SCHEMA

    def get_geocat_id_from_csw(self, cql=None, cql_query=None, cql_search_term=None):
        nextrecord = 0
        record_ids = []
        csw_args = {"maxrecords": 50, "startposition": nextrecord}

        if cql_query and cql_search_term:
            csw_args["constraints"] = [PropertyIsEqualTo(cql_query, cql_search_term)]
        elif cql:
            csw_args["cql"] = cql
        else:
            csw_args["constraints"] = [
                PropertyIsEqualTo(CQL_QUERY_DEFAULT, CQL_SEARCH_TERM_DEFAULT)
            ]

        while nextrecord is not None:
            csw_args["startposition"] = nextrecord
            self.csw.getrecords2(**csw_args)
            if self.csw.response is None or self.csw.results["matches"] == 0:
                raise CswNotFoundError(
                    f"No dataset found for url {self.csw.url} with arguments "
                    f"{csw_args}"
                )
            if self.csw.results["returned"] > 0:
                if 0 < self.csw.results["nextrecord"] <= self.csw.results["matches"]:
                    nextrecord = self.csw.results["nextrecord"]
                else:
                    nextrecord = None
                for id in list(self.csw.records.keys()):
                    record_ids.append(id)
        return record_ids

    def get_record_by_id(self, geocat_id):
        self.csw.getrecordbyid(id=[geocat_id], outputschema=self.schema)
        csw_record_as_string = self.csw.response
        if csw_record_as_string:
            return csw_record_as_string
        else:
            return None


class GeocatDcatCatalogueServiceWeb(object):
    """
    CSW client for ``geocat_ech0271_harvester`` (DCAT-AP-CH / eCH-0271).

    Uses explicit HTTP GetRecords / GetRecordById with OUTPUTSCHEMA DCAT-AP-CH,
    including batch GetRecords to avoid one request per record.
    """

    def __init__(self, url):
        self.csw = CatalogueServiceWeb(url)
        self.schema = DCAT_AP_CH_SCHEMA

    def get_geocat_id_from_csw(self, cql=None, cql_query=None, cql_search_term=None):
        """List identifiers via OWSLib (summary records); same constraints as classic."""
        nextrecord = 0
        record_ids = []
        csw_args = {"maxrecords": 50, "startposition": nextrecord}

        if cql_query and cql_search_term:
            csw_args["constraints"] = [PropertyIsEqualTo(cql_query, cql_search_term)]
        elif cql:
            csw_args["cql"] = cql
        else:
            csw_args["constraints"] = [
                PropertyIsEqualTo(CQL_QUERY_DEFAULT, CQL_SEARCH_TERM_DEFAULT)
            ]

        while nextrecord is not None:
            csw_args["startposition"] = nextrecord
            self.csw.getrecords2(**csw_args)
            if self.csw.response is None or self.csw.results["matches"] == 0:
                raise CswNotFoundError(
                    f"No dataset found for url {self.csw.url} with arguments "
                    f"{csw_args}"
                )
            if self.csw.results["returned"] > 0:
                if 0 < self.csw.results["nextrecord"] <= self.csw.results["matches"]:
                    nextrecord = self.csw.results["nextrecord"]
                else:
                    nextrecord = None
                for id in list(self.csw.records.keys()):
                    record_ids.append(id)
        return record_ids

    def get_record_by_id(self, geocat_id):
        params = {
            "SERVICE": "CSW",
            "VERSION": "2.0.2",
            "REQUEST": "GetRecordById",
            "OUTPUTSCHEMA": DCAT_AP_CH_SCHEMA,
            "ELEMENTSETNAME": "full",
            "id": geocat_id,
        }
        resp = requests.get(self.csw.url, params=params, timeout=60)
        resp.raise_for_status()
        body = resp.text
        if not body:
            return None
        if "ExceptionReport" in body or "ows:Exception" in body:
            raise CswNotFoundError(
                f"CSW error for GetRecordById id={geocat_id!r}: {body[:500]}"
            )
        return body

    def get_records_dcat(
        self, cql=None, cql_query=None, cql_search_term=None, maxrecords=50
    ):
        """
        Fetch all matching records in batch using GetRecords with the DCAT-AP-CH
        outputschema. Yields (geocat_id, wrapped_xml_string) tuples.
        """
        base_url = self.csw.url
        params = {
            "SERVICE": "CSW",
            "VERSION": "2.0.2",
            "REQUEST": "GetRecords",
            "OUTPUTSCHEMA": DCAT_AP_CH_SCHEMA,
            "TYPENAMES": "csw:Record",
            "ELEMENTSETNAME": "full",
            "RESULTTYPE": "results",
            "MAXRECORDS": str(maxrecords),
        }
        params.update(_build_cql_params(cql, cql_query, cql_search_term))

        start = 1
        seen_ids = set()
        while True:
            params["START"] = str(start)
            log.debug("GetRecords DCAT batch start=%s url=%s", start, base_url)
            resp = requests.get(base_url, params=params, timeout=60)
            resp.raise_for_status()

            try:
                root = etree.fromstring(resp.content)
            except etree.XMLSyntaxError as exc:
                raise CswNotFoundError(f"Could not parse GetRecords response: {exc}")

            datasets = list(root.iter(_DCAT_DATASET_TAG))
            if not datasets:
                break

            for dataset_elem in datasets:
                id_elem = dataset_elem.find(_DCT_IDENTIFIER_TAG)
                if id_elem is None or not id_elem.text:
                    log.warning("dcat:Dataset without dct:identifier, skipping")
                    continue
                geocat_id = id_elem.text.strip()
                if geocat_id in seen_ids:
                    log.warning(
                        "Duplicate dcat:Dataset id=%s in GetRecords batch, skipping",
                        geocat_id,
                    )
                    continue
                seen_ids.add(geocat_id)
                dataset_xml = etree.tostring(dataset_elem, encoding="unicode")
                yield geocat_id, _GETRECORDBYID_ENVELOPE.format(dataset_xml=dataset_xml)

            next_record = _next_record_from_results(root, start)
            if next_record is None:
                break
            start = next_record


class CswNotFoundError(Exception):
    pass
