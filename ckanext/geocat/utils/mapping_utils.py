import os
import rdflib
import yaml
from rdflib.namespace import Namespace, RDF, SKOS
from lxml import etree
import xml.etree.ElementTree as ET

import logging
log = logging.getLogger(__name__)

format_namespaces = {
  "skos": SKOS,
  "rdf": RDF,
}

media_types_namespaces = {
    'ns': 'http://www.iana.org/assignments'
}

DCT = Namespace("http://purl.org/dc/terms/")
SKOS = Namespace("http://www.w3.org/2004/02/skos/core#")
TERMS_OF_USE_OPEN = 'https://opendata.swiss/terms-of-use/#terms_open'
TERMS_OF_USE_BY = 'https://opendata.swiss/terms-of-use#terms_by'
TERMS_OF_USE_ASK = 'https://opendata.swiss/terms-of-use#terms_ask'
TERMS_OF_USE_BY_ASK = 'https://opendata.swiss/terms-of-use#terms_by_ask'
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


def get_format_values():
    g = rdflib.Graph()
    for prefix, namespace in format_namespaces.items():
        g.bind(prefix, namespace)
    file = os.path.join(__location__, 'formats.xml')
    g.parse(file, format='xml')
    format_values = {}
    for format_uri_ref in g.subjects():
        format_extension = format_uri_ref.split('/')[-1]
        format_values[format_extension] = format_uri_ref
    return format_values


def get_iana_media_type_values():
    file = os.path.join(__location__, 'iana_media_types.xml')
    tree = ET.parse(file)
    root = tree.getroot()
    records = root.findall('.//ns:record', media_types_namespaces)
    media_type_values = {}
    for record in records:
        if record.find('ns:file', media_types_namespaces) is None:
            continue
        if record.find('ns:name', media_types_namespaces) is None:
            continue
        name = record.find('ns:name', media_types_namespaces).text
        file_value = record.find('ns:file', media_types_namespaces).text
        media_type_values[name] = media_types_namespaces['ns']+'/'+file_value
    return media_type_values
