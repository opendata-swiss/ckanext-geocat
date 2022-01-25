import sys
from pprint import pprint
from ckan.lib.cli import CkanCommand
from ckanext.geocat.utils import csw_processor, csw_mapping
from ckanext.geocat.harvester import DEFAULT_PERMA_LINK_URL, DEFAULT_PERMA_LINK_LABEL  # noqa


class GeocatCommand(CkanCommand):

    '''Command to query geocat

    Usage::
    
    With this command you can query a remote csw source:
    
    'paster geocat list https://www.geocat.ch/geonetwork/srv/eng/csw-ZH/'
    
    The 'list'  command will bring back the record ids of the remote source.
    You can also add query arguments to it: this here for example will search
    for the keyword 'opendata.swiss' on the remote source:
    
    'paster geocat list https://www.geocat.ch/geonetwork/srv/eng/csw-ZH/ --key=keyword --term=opendata.swiss'
    
    Once you have the record ids, you can map a specific remote record: 
    
    'paster geocat dataset https://www.geocat.ch/geonetwork/srv/eng/csw-ZH/ 8ae7eeb1-04d4-4c78-93e1-4225412db6a4'
    
    The 'dataset' command uses the same mapping as the harvester, except some extras as the geocat-permalink and 
    some other fields that are taken from the harvester config when harvesting and just get defaults when
    the command is used. 
    '''  # noqa
    summary = __doc__.split('\n')[0]
    usage = __doc__

    def __init__(self, name):
        super(CkanCommand, self).__init__(name)
        self.parser.add_option(
            '--query', action="store", type="string",  dest='cql_query',
            default=csw_processor.CQL_QUERY_DEFAULT,
            help='key for cql search')
        self.parser.add_option(
            '--term', action="store", type="string",  dest='cql_term',
            default=csw_processor.CQL_SEARCH_TERM_DEFAULT,
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

        cqlquery = self.options.cql_query or csw_processor.CQL_QUERY_DEFAULT
        cqlterm = self.options.cql_term \
            or csw_processor.CQL_SEARCH_TERM_DEFAULT

        try:
            csw_data = csw_processor.GeocatCatalogueServiceWeb(url=url)
            search_result = csw_data.get_geocat_id_from_csw(
                cqlquery=cqlquery, cqlterm=cqlterm)
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
            csw_data = csw_processor.GeocatCatalogueServiceWeb(url=url)

            xml = csw_data.get_record_by_id(id)
            self.csw_map = csw_mapping.GeoMetadataMapping(
                organization_slug="swisstopo",
                geocat_perma_link=DEFAULT_PERMA_LINK_URL,
                geocat_perma_label=DEFAULT_PERMA_LINK_LABEL,
                legal_basis_url="",
                default_rights="",
                valid_identifiers=[],
            )
            dataset = self.csw_map.get_metadata(xml, id)
        except Exception as e:
            print("Got error %r when searching at remote url %r for record id %r" % (e, url, id))  # noqa
            self.helpCmd()
            sys.exit(1)

        print("\nDataset:")
        pprint(dataset)
