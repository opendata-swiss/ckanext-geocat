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

DOWNLOAD_PROTOCOL = "WWW:DOWNLOAD"
OGC_WMTS_PROTOCOL = "OGC:WMTS"
OGC_WFS_PROTOCOL = "OGC:WFS"
OGC_WMS_PROTOCOL = "OGC:WMS"
LINKED_DATA_PROTOCOL = "LINKED:DATA"
ESRI_REST_PROTOCOL = "ESRI:REST"
MAP_PROTOCOL = 'MAP:Preview'
SERVICE_PROTOCOLS = [OGC_WMTS_PROTOCOL, OGC_WFS_PROTOCOL, OGC_WMS_PROTOCOL, LINKED_DATA_PROTOCOL, ESRI_REST_PROTOCOL, MAP_PROTOCOL]  # noqa
SERVICE_FORMAT = 'SERVICE'


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


def xpath_get_url_and_languages(node):
    URL_PATH_LIST = [
        './/gmd:linkage//che:LocalisedURL[@locale="#DE"]/text()',
        './/gmd:linkage//che:LocalisedURL[@locale="#FR"]/text()',
        './/gmd:linkage//che:LocalisedURL[@locale="#EN"]/text()',
        './/gmd:linkage//che:LocalisedURL[@locale="#IT"]/text()',
        './/che:LocalisedURL/text()',
        './/gmd:URL/text()',
    ]
    languages = []
    url = xpath_get_first_of_values_from_path_list(node=node, path_list=URL_PATH_LIST)  # noqa
    for locale in LOCALES:
        value_locale = node.xpath('.//che:LocalisedURL[@locale="#{}"]'.format(locale) + '/text()',  # noqa
                                  namespaces=gmd_namespaces)
        if value_locale:
            languages.append(locale.lower())
    return url, languages


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


def xpath_get_distribution_from_distribution_node(resource_node, protocol, download_formats, service_formats):  # noqa
    GMD_RESOURCE_NAME = './/gmd:name/gco:CharacterString/text()'
    GMD_RESOURCE_DESCRIPTION = './/gmd:description'
    distribution = {}
    distribution['name'] = xpath_get_single_sub_node_for_node_and_path(node=resource_node, path=GMD_RESOURCE_NAME)  # noqa
    description_node = xpath_get_single_sub_node_for_node_and_path(node=resource_node, path=GMD_RESOURCE_DESCRIPTION)  # noqa
    if len(description_node):
        distribution['description'] = xpath_get_language_dict_from_geocat_multilanguage_node(description_node)  # noqa
    else:
        distribution['description'] = {'en': '', 'it': '', 'de': '', 'fr': ''}
    normed_protocol, protocol_name = _get_normed_protocol(protocol)
    distribution['protocol'] = normed_protocol
    distribution['protocol_name'] = protocol_name
    if normed_protocol == DOWNLOAD_PROTOCOL and protocol.startswith(DOWNLOAD_PROTOCOL + ':'):  # noqa
        format = protocol.strip(DOWNLOAD_PROTOCOL + ':')
        if format in download_formats:
            distribution['format'] = format
    if normed_protocol in SERVICE_PROTOCOLS:
        format = SERVICE_FORMAT
        if format in service_formats:
            distribution['format'] = format
    GMD_URL = './/gmd:linkage'
    url_node = xpath_get_single_sub_node_for_node_and_path(node=resource_node, path=GMD_URL)  # noqa
    if url_node:
        distribution['url'], distribution['language'] = xpath_get_url_and_languages(url_node)  # noqa
    return distribution


def _get_normed_protocol(protocol):
    protocol_to_name_mapping = {
        OGC_WMTS_PROTOCOL: "WMTS (GetCapabilities)",
        OGC_WMS_PROTOCOL: "WMS (GetCapabilities)",
        OGC_WFS_PROTOCOL: "WFS (GetCapabilities)",
        DOWNLOAD_PROTOCOL: "Download",
        LINKED_DATA_PROTOCOL: "Linked Data (Dienst)",
        MAP_PROTOCOL: "Map (Preview)",
        ESRI_REST_PROTOCOL: "ESRI (Rest)"
    }
    for normed_protocol in protocol_to_name_mapping.items():
        if protocol.startswith(normed_protocol):
            return normed_protocol, protocol_to_name_mapping.get(normed_protocol)  # noqa
    return None, None


def _clean_string(value):
    return re.sub('\s+', ' ', value).strip()


class MetadataFormatError(Exception):
    pass
