import sys
from pprint import pprint

from ckan.lib.cli import CkanCommand

from ckanext.geocat.harvester import (
    DEFAULT_PERMA_LINK_LABEL,
    DEFAULT_PERMA_LINK_URL,
)
from ckanext.geocat.utils import csw_mapping, csw_processor


# TODO: Update these commands to use the IClick interface:
# https://docs.ckan.org/en/2.11/extensions/plugin-interfaces.html#ckan.plugins.interfaces.IClick
class GeocatCommand(CkanCommand):
    """Command to query geocat

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
    """

    summary = __doc__.split("\n")[0]
    usage = __doc__

    def __init__(self, name):
        super(CkanCommand, self).__init__(name)
        self.parser.add_option(
            "--query",
            action="store",
            type="string",
            dest="cql_query",
            default=csw_processor.CQL_QUERY_DEFAULT,
            help="key for cql search",
        )
        self.parser.add_option(
            "--term",
            action="store",
            type="string",
            dest="cql_term",
            default=csw_processor.CQL_SEARCH_TERM_DEFAULT,
            help="searchterm for cql search",
        )

    def command(self):
        self._load_config()
        options = {
            "dataset": self.dataset_command,
            "list": self.list_command,
            "help": self.help_command,
        }
        try:
            cmd = self.args[0]
            options[cmd](*self.args[1:])
        except (KeyError, IndexError):
            self.help_command()

    def help_command(self):
        print(self.__doc__)

    def list_command(self, url=None):
        if len(self.args) >= 2:
            url = str(self.args[1])
        else:
            print("Expected remote url")
            self.help_command()
            sys.exit(1)

        cqlquery = self.options.cql_query or csw_processor.CQL_QUERY_DEFAULT
        cqlterm = self.options.cql_term or csw_processor.CQL_SEARCH_TERM_DEFAULT

        try:
            csw_data = csw_processor.GeocatCatalogueServiceWeb(url=url)
            search_result = csw_data.get_geocat_id_from_csw(
                cql_query=cqlquery, cql_search_term=cqlterm
            )
            print(f"Search result for {url!r}")
            print(f"CQL query: {cqlquery}: {cqlterm}")
            for record_id in search_result:
                print(f"geocat_id: {record_id!r}")
        except Exception as e:
            print(f"Got error {e!r} when searching remote url {url!r}")
            self.help_command()
            sys.exit(1)

    def dataset_command(self, url=None, id=None):
        if len(self.args) >= 3:
            url = str(self.args[1])
            id = str(self.args[2])
        else:
            print("Expected remote url and record id")
            self.help_command()
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
            print(
                f"Got error {e!r} when searching at remote url {url!r} "
                f"for record id {id!r}"
            )
            self.help_command()
            sys.exit(1)

        print("\nDataset:")
        pprint(dataset)
