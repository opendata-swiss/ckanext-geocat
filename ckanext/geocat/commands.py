import sys
from pprint import pprint
import ckan.lib.cli
import ckanext.geocat.metadata as md
import ckanext.geocat.xml_loader as loader


class GeocatCommand(ckan.lib.cli.CkanCommand):

    '''Command to query geocat

    Usage::

            paster geocat search birds
            paster geocat cql "csw:AnyText like '%birds%'"
            paster geocat list "keyword = 'opendata.swiss'" https://www.geocat.ch/geonetwork/srv/eng/csw-ZH/
            paster geocat dataset "8ae7eeb1-04d4-4c78-93e1-4225412db6a4" https://www.geocat.ch/geonetwork/srv/eng/csw-ZH/

    '''  # noqa
    summary = __doc__.split('\n')[0]
    usage = __doc__
    DEFAULT_CSW_SERVER = 'http://www.geocat.ch/geonetwork/srv/eng/csw'
    DEFAULT_CQL = "keyword = 'opendata.swiss'"

    def command(self):
        options = {
            'search': self.searchCmd,
            'cql': self.cqlCmd,
            'dataset': self.datasetCmd,
            'list': self.listCmd,
            'help': self.helpCmd,
        }

        try:
            cmd = self.args[0]
            options[cmd](*self.args[1:])
        except (KeyError, IndexError):
            self.helpCmd()

    def helpCmd(self):
        print(self.__doc__)

    def cqlCmd(self, query=None, csw_url=None):
        if (query is None):
            print("Argument 'query' must be set")
            self.helpCmd()
            sys.exit(1)
        if csw_url is None:
            csw_url = self.DEFAULT_CSW_SERVER
        csw = md.CswHelper(url=csw_url.rstrip('/'))
        for xml, value in csw.get_by_search(cql=query):
            print(xml)

    def listCmd(self, cql=None, csw_url=None):
        if cql is None:
            cql = self.DEFAULT_CQL
        if csw_url is None:
            csw_url = self.DEFAULT_CSW_SERVER

        csw = md.CswHelper(url=csw_url.rstrip('/'))

        print("CQL query: %s" % cql)
        for record_id in csw.get_id_by_search(cql=cql):
            print('ID: %r' % record_id)

    def datasetCmd(self, id=None, csw_url=None):
        if id is None:
            print("Argument 'id' must be set")
            self.helpCmd()
            sys.exit(1)
        if csw_url is None:
            csw_url = self.DEFAULT_CSW_SERVER

        csw = md.CswHelper(url=csw_url.rstrip('/'))
        print("ID: %s\n" % id)

        xml = csw.get_by_id(id)
        print("XML: %s" % xml)
        xml_elem = loader.from_string(xml)
        dataset_metadata = md.GeocatDcatDatasetMetadata()
        dist_metadata = md.GeocatDcatDistributionMetadata()

        print("\nDataset:")
        pprint(dataset_metadata.get_metadata(xml_elem))

        print("\nDistributions:")
        pprint(dist_metadata.get_metadata(xml_elem))

    def searchCmd(self, query=None, csw_url=None):
        if (query is None):
            print("Argument 'query' must be set")
            self.helpCmd()
            sys.exit(1)
        if csw_url is None:
            csw_url = self.DEFAULT_CSW_SERVER
        csw = md.CswHelper(url=csw_url.rstrip('/'))
        for xml, value in csw.get_by_search(query):
            print(xml)
