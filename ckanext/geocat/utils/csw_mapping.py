# -*- coding: utf-8 -*-

from ckanext.geocat.utils import ogdch_map_utils, xpath_utils  # noqa

LOCALES = ['DE', 'FR', 'EN', 'IT']

gmd_namespaces = {
    'atom': 'http://www.w3.org/2005/Atom',
    'che': 'http://www.geocat.ch/2008/che',
    'csw': 'http://www.opengis.net/cat/csw/2.0.2',
    'dc': 'http://purl.org/dc/elements/1.1/',
    'dct': 'http://purl.org/dc/terms/',
    'ddi': 'http://www.icpsr.umich.edu/DDI',
    'dif': 'http://gcmd.gsfc.nasa.gov/Aboutus/xml/dif/',
    'fgdc': 'http://www.opengis.net/cat/csw/csdgm',
    'gco': 'http://www.isotc211.org/2005/gco',
    'gmd': 'http://www.isotc211.org/2005/gmd',
    'gmx': 'http://www.isotc211.org/2005/gmx',
    'gml': 'http://www.opengis.net/gml',
    'ogc': 'http://www.opengis.net/ogc',
    'ows': 'http://www.opengis.net/ows',
    'rim': 'urn:oasis:names:tc:ebxml-regrep:xsd:rim:3.0',
    'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
    'srv': 'http://www.isotc211.org/2005/srv',
    'xs': 'http://www.w3.org/2001/XMLSchema',
    'xs2': 'http://www.w3.org/XML/Schema',
    'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
    'xlink': 'http://www.w3.org/1999/xlink',
}


class GeodataMapping(object):

    def __init__(self, organization_slug, geocat_perma_link, geocat_perma_label, default_rights):  # noqa
        self.geocat_perma_link = geocat_perma_link
        self.geocat_perma_label = geocat_perma_label
        self.organization_slug = organization_slug
        self.default_rights = default_rights

    def get_matadat(self, csw_record_as_string, geocat_id):
        root_node = get_elem_tree_from_string(csw_record_as_string)
        dataset_dict = {}
        dataset_dict['identifier'] = \
            _map_dataset_identifier(
                node=root_node,
                organization_slug=self.organization_slug)
        return dataset_dict


def _map_dataset_identifier(node, organization_slug):
    GMD_IDENTIFIER = './/gmd:fileIdentifier/gco:CharacterString/text()'
    geocat_identifier = xpath_utils.xpath_get_single_sub_node_for_node_and_path(node=node, path=GMD_IDENTIFIER)  # noqa
    if geocat_identifier:
        return ogdch_map_utils.map_geocat_to_ogdch_identifier(geocat_identifier, organization_slug)  # noqa
