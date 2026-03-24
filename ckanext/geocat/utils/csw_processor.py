import logging

import requests
from lxml import etree
from owslib.catalogue.csw2 import CatalogueServiceWeb
from owslib.fes import PropertyIsEqualTo

log = logging.getLogger(__name__)

CHE_SCHEMA = "http://www.geocat.ch/2008/che"  # kept for reference
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


class GeocatCatalogueServiceWeb(object):
    def __init__(self, url):
        self.csw = CatalogueServiceWeb(url)
        self.schema = DCAT_AP_CH_SCHEMA

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
        """Fetch a single record by UUID. Returns the raw XML response string."""
        self.csw.getrecordbyid(id=[geocat_id], outputschema=self.schema)
        csw_record_as_string = self.csw.response
        if csw_record_as_string:
            return csw_record_as_string
        else:
            return None

    def get_records_dcat(self, cql=None, cql_query=None, cql_search_term=None,
                         maxrecords=50):
        """
        Fetch all matching records in batch using GetRecords with the DCAT-AP-CH
        outputschema. Returns a generator of (geocat_id, wrapped_xml_string) tuples.

        Each ``wrapped_xml_string`` is a GetRecordByIdResponse envelope containing
        a single dcat:Dataset, ready to be passed directly to
        ``DcatMetadataMapping.get_metadata()``.

        This avoids one HTTP request per record and is preferred over calling
        ``get_geocat_id_from_csw`` + ``get_record_by_id`` in a loop.
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
        if cql_query and cql_search_term:
            params["CONSTRAINTLANGUAGE"] = "CQL_TEXT"
            params["CONSTRAINT_LANGUAGE_VERSION"] = "1.1.0"
            params["CONSTRAINT"] = f"{cql_query} = '{cql_search_term}'"
        elif cql:
            params["CONSTRAINTLANGUAGE"] = "CQL_TEXT"
            params["CONSTRAINT_LANGUAGE_VERSION"] = "1.1.0"
            params["CONSTRAINT"] = cql
        else:
            params["CONSTRAINTLANGUAGE"] = "CQL_TEXT"
            params["CONSTRAINT_LANGUAGE_VERSION"] = "1.1.0"
            params["CONSTRAINT"] = (
                f"{CQL_QUERY_DEFAULT} = '{CQL_SEARCH_TERM_DEFAULT}'"
            )

        start = 1
        while True:
            params["START"] = str(start)
            log.debug("GetRecords DCAT batch start=%s url=%s", start, base_url)
            resp = requests.get(base_url, params=params, timeout=60)
            resp.raise_for_status()
            raw = resp.content  # bytes

            try:
                root = etree.fromstring(raw)
            except etree.XMLSyntaxError as exc:
                raise CswNotFoundError(f"Could not parse GetRecords response: {exc}")

            datasets = list(root.iter(_DCAT_DATASET_TAG))
            if not datasets:
                break

            for dataset_elem in datasets:
                # Extract dct:identifier
                id_elem = dataset_elem.find(_DCT_IDENTIFIER_TAG)
                if id_elem is None or not id_elem.text:
                    log.warning("dcat:Dataset without dct:identifier, skipping")
                    continue
                geocat_id = id_elem.text.strip()

                # Re-serialise the single dataset element
                dataset_xml = etree.tostring(dataset_elem, encoding="unicode")
                wrapped = _GETRECORDBYID_ENVELOPE.format(dataset_xml=dataset_xml)
                yield geocat_id, wrapped

            # Pagination: check SearchResults attributes
            ns = {"csw": "http://www.opengis.net/cat/csw/2.0.2"}
            sr = root.find(".//csw:SearchResults", ns)
            if sr is None:
                break
            next_record = int(sr.get("nextRecord", 0))
            matched = int(sr.get("numberOfRecordsMatched", 0))
            returned = int(sr.get("numberOfRecordsReturned", 0))
            log.debug(
                "GetRecords: matched=%s returned=%s nextRecord=%s",
                matched, returned, next_record,
            )
            if next_record == 0 or next_record > matched or returned == 0:
                break
            start = next_record


class CswNotFoundError(Exception):
    pass
