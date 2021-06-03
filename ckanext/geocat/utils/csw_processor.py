# -*- coding: utf-8 -*-

from owslib.csw import CatalogueServiceWeb
from owslib.fes import PropertyIsEqualTo

import logging
log = logging.getLogger(__name__)

CHE_SCHEMA = 'http://www.geocat.ch/2008/che'
CQL_QUERY_DEFAUL = 'keyword'
CQL_SEARCH_TERM_DEFAUT = 'opendata.swiss'


class GeocatCatalogueServiceWeb(object):
    def __init__(self, url):
        self.csw = CatalogueServiceWeb(url)
        self.schema = CHE_SCHEMA

    def get_geocat_id_from_csw(self, cqlquery=CQL_QUERY_DEFAUL, cqlvalue=CQL_SEARCH_TERM_DEFAUT):  # noqa
        harvest_query = PropertyIsEqualTo(cqlquery, cqlvalue)
        nextrecord = 0
        record_ids = []
        while nextrecord is not None:
            self.csw.getrecords2(constraints=[harvest_query], maxrecords=50, startposition=nextrecord)  # noqa
            if (self.csw.response is None or self.csw.results['matches'] == 0):
                raise CswNotFoundError("No dataset found for harvest query {}".format(harvest_query))  # noqa
            if self.csw.results['returned'] > 0:
                if self.csw.results['nextrecord'] > 0:
                    nextrecord = self.csw.results['nextrecord']
                else:
                    nextrecord = None
                for id in self.csw.records.keys():
                    record_ids.append(id)
        log.error(record_ids)
        return record_ids

    def get_record_by_id(self, geocat_id):
        self.csw.getrecordbyid(id=[geocat_id], outputschema=self.schema)
        csw_record_as_string = self.csw.response
        if csw_record_as_string:
            return csw_record_as_string
        else:
            return None


class CswNotFoundError(Exception):
    pass
