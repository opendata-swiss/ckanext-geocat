import os
import rdflib
import yaml
from rdflib.namespace import Namespace
from lxml import etree

import logging
log = logging.getLogger(__name__)

DCT = Namespace("http://purl.org/dc/terms/")
SKOS = Namespace("http://www.w3.org/2004/02/skos/core#")
TERMS_OF_USE_OPEN = 'NonCommercialAllowed-CommercialAllowed-ReferenceNotRequired' # noqa
TERMS_OF_USE_BY = 'NonCommercialAllowed-CommercialAllowed-ReferenceRequired' # noqa
TERMS_OF_USE_ASK = 'NonCommercialAllowed-CommercialWithPermission-ReferenceNotRequired' # noqa
TERMS_OF_USE_BY_ASK = 'NonCommercialAllowed-CommercialWithPermission-ReferenceRequired' # noqa
VALID_TERMS_OF_USE = [
    TERMS_OF_USE_BY,
    TERMS_OF_USE_ASK,
    TERMS_OF_USE_BY_ASK,
    TERMS_OF_USE_OPEN
]
DEFAULT_TERMS_OF_USE = TERMS_OF_USE_BY

namespaces = {
  "skos": SKOS,
  "dc11": "http://purl.org/dc/elements/1.1/",
  "foaf": "http://xmlns.com/foaf/0.1/",
  "dc": DCT
}

__location__ = \
    os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))


def get_elem_tree_from_string(xml_string):
    try:
        xml_elem_tree = etree.fromstring(xml_string)
    except etree.XMLSyntaxError as e:
        raise MetadataFormatError('Could not parse XML: %r' % e)
    return xml_elem_tree


class MetadataFormatError(Exception):
    pass


def get_terms_of_use():
    g = rdflib.Graph()
    for prefix, namespace in namespaces.items():
        g.bind(prefix, namespace)
    file = os.path.join(__location__, 'geocat-terms-of-use.xml')
    g.parse(file, format='xml')
    return g


def get_excluded_protocols():
    try:
        mapping_path = os.path.join(__location__, 'mapping.yaml')
        with open(mapping_path, 'r') as mapping_file:
            mapping = yaml.safe_load(mapping_file)
            return mapping.get('EXCLUDED_PROTOCOLS')
    except KeyError:
        log.error("No blacklist of protocols could be found in mapping_path {}"
                  .format(mapping_path))
    except (IOError, yaml.YAMLError):
        log.error("Mapping_path for protocol blacklist could not be opened {}"
                  .format(mapping_path))
