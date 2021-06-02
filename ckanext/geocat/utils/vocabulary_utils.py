import os
import rdflib
from rdflib.namespace import Namespace
from lxml import etree

DCT = Namespace("http://purl.org/dc/terms/")
SKOS = Namespace("http://www.w3.org/2004/02/skos/core#")

namespaces = {
  "skos": SKOS,
  "dc11": "http://purl.org/dc/elements/1.1/",
  "foaf": "http://xmlns.com/foaf/0.1/",
  "dc": DCT
}

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))  # noqa


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
