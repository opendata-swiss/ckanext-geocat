import sys
from pprint import pprint
from ckan.lib.cli import CkanCommand
import ckanext.geocat.metadata as md
import ckanext.geocat.xml_loader as loader
from ckanext.geocat.utils import csw_processor, csw_mapping
from ckanext.geocat.harvester import DEFAULT_PERMA_LINK_URL, DEFAULT_PERMA_LINK_LABEL


class GeocatCommand(CkanCommand):

    '''Command to query geocat

    Usage::

            paster geocat list https://www.geocat.ch/geonetwork/srv/eng/csw-ZH/ --key=keyword --term=opendata.swiss
            paster geocat list https://www.geocat.ch/geonetwork/srv/eng/csw-ZH/
            paster geocat dataset https://www.geocat.ch/geonetwork/srv/eng/csw-ZH/ 8ae7eeb1-04d4-4c78-93e1-4225412db6a4

    '''  # noqa
    summary = __doc__.split('\n')[0]
    usage = __doc__
    DEFAULT_CSW_SERVER = 'https://geocat-int.dev.bgdi.ch/geonetwork/srv/ger/csw-opendata-testgroup'
    DEFAULT_CQL = "keyword=opendata.swiss"

    def __init__(self, name):
        super(CkanCommand, self).__init__(name)
        self.parser.add_option(
            '--query', action="store", type="string",  dest='cql_query',
            default=csw_processor.CQL_QUERY_DEFAUL,
            help='key for cql search')
        self.parser.add_option(
            '--term', action="store", type="string",  dest='cql_term',
            default=csw_processor.CQL_SEARCH_TERM_DEFAUT,
            help='searchterm for cql search')

    def command(self):
        self._load_config()
        options = {
            'dataset': self.datasetCmd,
            'list': self.listCmd,
            'help': self.helpCmd,
        }
        try:
            cmd = self.args[0]
            import pdb;pdb.set_trace()
            options[cmd](*self.args[1:])
        except (KeyError, IndexError):
            self.helpCmd()

    def helpCmd(self):
        print(self.__doc__)

    def listCmd(self, url=None):
        if len(self.args) >= 2:
            url = unicode(self.args[1])
        else:
            print("Expected remote url")
            self.helpCmd()
            sys.exit(1)

        cqlquery = self.options.get('cql_query', csw_processor.CQL_QUERY_DEFAUL)
        cqlterm = self.options.get('cql_term', csw_processor.CQL_SEARCH_TERM_DEFAUT)

        try:
            csw_data = csw_processor.GeocatCatalogueServiceWeb(url=url, cqlquery=cqlquery, cqlvalue=cqlterm)  # noqa
            search_result = csw_data.get_geocat_id_from_csw()
            print("Search result for %r" % url)
            print("CQL query: %s: %s" % (cqlquery, cqlterm))
            for record_id in search_result:
                print('geocat_id: %r' % record_id)
        except Exception as e:
            print("Got error %r when searching remote url %r" % (e, url))
            self.helpCmd()
            sys.exit(1)

    def datasetCmd(self, url=None, id=None):
        if len(self.args) >= 3:
            url = unicode(self.args[1])
            id = unicode(self.args[2])
        else:
            print("Expected remote url and record id")
            self.helpCmd()
            sys.exit(1)

        try:
            import pdb; pdb.set_trace()
            csw_data = csw_processor.GeocatCatalogueServiceWeb(url=url)

            xml = csw_data.get_record_by_id(id)
            self.csw_map = csw_mapping.GeoMetadataMapping(
                organization_slug="swisstopo",
                geocat_perma_link=DEFAULT_PERMA_LINK_URL,
                geocat_perma_label=DEFAULT_PERMA_LINK_LABEL,
                legal_basis_url="",
                valid_identifiers=[],
            )
            dataset = self.csw_map.get_metadata(xml, id)
        except Exception as e:
            print("Got error %r when searching at remote url %r for record id %r" % (e, url, id))
            self.helpCmd()
            sys.exit(1)

        print("\nDataset:")
        pprint(dataset)

