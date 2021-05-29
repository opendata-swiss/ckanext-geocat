# -*- coding: utf-8 -*-

import re
from lxml import etree

LOCALES = ['DE', 'FR', 'EN', 'IT']
XPATH_NODE = 'node'
XPATH_TEXT = 'text'


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


def get_elem_tree_from_string(xml_string):
    try:
        xml_elem_tree = etree.fromstring(xml_string)
    except etree.XMLSyntaxError as e:
        raise MetadataFormatError('Could not parse XML: %r' % e)
    return xml_elem_tree


def xpath_get_single_sub_node_for_node_and_path(node, path):
    results = node.xpath(path, namespaces=gmd_namespaces)
    if results:
        return results[0]
    else:
        return ''


def xpath_get_all_sub_nodes_for_node_and_path(node, path):
    results = node.xpath(path, namespaces=gmd_namespaces)
    if results:
        return results
    else:
        return []


def xpath_get_all_values_for_node_and_path_list(node, path_list):
    values = []
    for path in path_list:
        value = node.xpath(path, namespaces=gmd_namespaces)
        if value:
            values.extend(value)
    return values


def xpath_get_first_of_values_from_path_list(node, path_list, get=XPATH_NODE):
    get_text = ''
    if get == XPATH_TEXT:
        get_text = '/text()'
    for path in path_list:
        value = node.xpath(path + get_text, namespaces=gmd_namespaces)
        if value:
            return value[0]


def xpath_get_language_dict_from_geocat_multilanguage_node(node):
    language_dict = {'en': '', 'it': '', 'de': '', 'fr': ''}
    try:
        for locale in LOCALES:
            value_locale = node.xpath('.//gmd:textGroup/gmd:LocalisedCharacterString[@locale="#{}"]'.format(locale) + '/text()',  # noqa
                                      namespaces=gmd_namespaces)
            if value_locale:
                language_dict[locale.lower()] = _clean_string(value_locale[0])
        return language_dict
    except:
        value = node.xpath('.//gmd:CharacterString/text()',
                           namespaces=gmd_namespaces)
        return value


def xpath_get_rights_dict_form_rights_node(node):
    rights_dict = {'en': '', 'it': '', 'de': '', 'fr': '', 'anchor': ''}
    try:
        anchor = node.xpath('.//gmx:Anchor/text()', namespaces=gmd_namespaces)
        if anchor:
            rights_dict['anchor'] = anchor[0]
        for locale in LOCALES:
            value_locale = node.xpath('.//gmd:textGroup/gmd:LocalisedCharacterString[@locale="#{}"]'.format(locale) + '/text()',  # noqa
                                      namespaces=gmd_namespaces)
            if value_locale:
                rights_dict[locale.lower()] = _clean_string(value_locale[0])
        return rights_dict
    except:
        return ''


def xpath_get_one_value_from_geocat_multilanguage_node(node):
    value = node.xpath('.//gmd:CharacterString/text()',
                       namespaces=gmd_namespaces)
    if value:
        return value
    for locale in LOCALES:
        value_locale = node.xpath('.//gmd:textGroup/gmd:LocalisedCharacterString[@locale="#{}"]'.format(locale) + '/text()',  # noqa
                                  namespaces=gmd_namespaces)
        if value_locale:
            return value_locale


def xpath_get_url_with_label_from_distribution(node):
    url = {}
    url_node = node.xpath('.//gmd:linkage/gmd:URL/text()',
                          namespaces=gmd_namespaces)
    if url_node:
        url = {'label': url_node[0], 'url': url_node[0]}
    text_node = node.xpath('.//gmd:description',
                           namespaces=gmd_namespaces)
    if text_node:
        url_text_node = xpath_get_one_value_from_geocat_multilanguage_node(text_node[0])  # noqa
        if url_text_node:
            url['label'] = url_text_node[0]
    return url


def _clean_string(value):
    return re.sub('\s+', ' ', value).strip()


class MetadataFormatError(Exception):
    pass
