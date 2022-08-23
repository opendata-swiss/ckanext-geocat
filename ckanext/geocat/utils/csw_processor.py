# -*- coding: utf-8 -*-

from owslib.csw import CatalogueServiceWeb

import logging
log = logging.getLogger(__name__)

CHE_SCHEMA = 'http://www.geocat.ch/2008/che'
CQL_QUERY_DEFAULT = 'subject'
CQL_SEARCH_TERM_DEFAULT = 'opendata.swiss'


class GeocatCatalogueServiceWeb(object):
    def __init__(self, url):
        self.csw = CatalogueServiceWeb(url)
        self.schema = CHE_SCHEMA

    def get_geocat_id_from_csw(self, cql):
        nextrecord = 0
        record_ids = []

        if cql is None:
            cql = "{} = '{}'"\
                .format(CQL_QUERY_DEFAULT, CQL_SEARCH_TERM_DEFAULT)

        while nextrecord is not None:
            self.csw.getrecords2(cql=cql,
                                 maxrecords=50,
                                 startposition=nextrecord)
            if self.csw.response is None or self.csw.results['matches'] == 0:
                raise CswNotFoundError("No dataset found for cql {}"
                                       .format(cql))
            if self.csw.results['returned'] > 0:
                if 0 < self.csw.results['nextrecord']\
                        <= self.csw.results['matches']:
                    nextrecord = self.csw.results['nextrecord']
                else:
                    nextrecord = None
                for id in self.csw.records.keys():
                    record_ids.append(id)
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
