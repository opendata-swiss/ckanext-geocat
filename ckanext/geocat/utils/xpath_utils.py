# -*- coding: utf-8 -*-

import re
from lxml import etree

import logging
log = logging.getLogger(__name__)

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

GMD_URL_LABEL = './/gmd:description'
GMD_SERVICE_NODES = '//gmd:identificationInfo//srv:containsOperations/srv:SV_OperationMetadata[.//srv:operationName//gco:CharacterString/text()]'  # noqa
GMD_SERVICE_URLS = [
    './/srv:connectPoint//gmd:linkage//che:LocalisedURL[@locale = "#DE" and ./text()]/text()',  # noqa
    './/srv:connectPoint//gmd:linkage//che:LocalisedURL[@locale = "#FR" and ./text()]/text()',  # noqa
    './/srv:connectPoint//gmd:linkage//che:LocalisedURL[@locale = "#EN" and ./text()]/text()',  # noqa
    './/srv:connectPoint//gmd:linkage//che:LocalisedURL[@locale = "#IT" and ./text()]/text()',  # noqa
    './/srv:connectPoint//gmd:linkage//che:LocalisedURL[./text()]/text()',  # noqa
]
GMD_MEDIA_TYPE = '//gmd:identificationInfo//srv:serviceType/gco:LocalName/text()'  # noqa
GMD_SERVICE_TITLE = './/srv:operationName/gco:CharacterString/text()'  # noqa
URL_PATH_LIST = [
    './/gmd:linkage//che:LocalisedURL[@locale="#DE"]/text()',
    './/gmd:linkage//che:LocalisedURL[@locale="#FR"]/text()',
    './/gmd:linkage//che:LocalisedURL[@locale="#EN"]/text()',
    './/gmd:linkage//che:LocalisedURL[@locale="#IT"]/text()',
    './/che:LocalisedURL/text()',
    './/gmd:URL/text()',
]
GMD_RESOURCE_NAME = './/gmd:name'
GMD_RESOURCE_DESCRIPTION = './/gmd:description'

DOWNLOAD_PROTOCOL = "WWW:DOWNLOAD"
OGC_WMTS_PROTOCOL = "OGC:WMTS"
OGC_WFS_PROTOCOL = "OGC:WFS"
OGC_WMS_PROTOCOL = "OGC:WMS"
LINKED_DATA_PROTOCOL = "LINKED:DATA"
APP_PROTOCOL = "WWW:DOWNLOAD-APP"
ESRI_REST_PROTOCOL = "ESRI:REST"
MAP_PROTOCOL = 'MAP:Preview'
NORMED_PROTOCOLS = [OGC_WMTS_PROTOCOL, OGC_WFS_PROTOCOL,
                    OGC_WMS_PROTOCOL, LINKED_DATA_PROTOCOL,
                    ESRI_REST_PROTOCOL, MAP_PROTOCOL,
                    APP_PROTOCOL, DOWNLOAD_PROTOCOL]
SERVICE_PROTOCOLS = [protocol for protocol in NORMED_PROTOCOLS
                     if protocol != DOWNLOAD_PROTOCOL]
FORMATED_SERVICE_PROTOCOLS = [
    protocol
    for protocol in SERVICE_PROTOCOLS
    if protocol not in [LINKED_DATA_PROTOCOL, MAP_PROTOCOL]
]
SERVICE_FORMAT = 'SERVICE'
API_FORMAT = "API"


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
        return None


def xpath_get_all_sub_nodes_for_node_and_path(node, path):
    results = node.xpath(path, namespaces=gmd_namespaces)
    if results:
        return results
    else:
        return None


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
            return value[0], path
    return None, None


def xpath_get_language_dict_from_geocat_multilanguage_node(node):
    language_dict = {'en': '', 'it': '', 'de': '', 'fr': ''}
    localised_string_found = False
    for locale in LOCALES:
        value_locale = \
            node.xpath('.//gmd:textGroup/gmd:LocalisedCharacterString[@locale="#{}"]/text()'  # noqa
                       .format(locale),
                       namespaces=gmd_namespaces)
        if value_locale:
            localised_string_found = True
            cleaned_value = _clean_string(value_locale[0])
            language_dict[locale.lower()] = cleaned_value
    if localised_string_found:
        return language_dict
    value = node.xpath('.//gco:CharacterString/text()',
                       namespaces=gmd_namespaces)
    if value:
        cleaned_value = _clean_string(value[0])
        for locale in LOCALES:
            language_dict[locale.lower()] = cleaned_value
        return language_dict
    return language_dict


def xpath_get_url_and_languages(node):
    languages = []
    url, _ = xpath_get_first_of_values_from_path_list(
        node=node, path_list=URL_PATH_LIST)
    for locale in LOCALES:
        value_locale = \
            node.xpath('.//che:LocalisedURL[@locale="#{}"]'
                       .format(locale) + '/text()',
                       namespaces=gmd_namespaces)
        if value_locale:
            languages.append(locale.lower())
    return url, languages


def xpath_get_rights_dict_form_rights_node(node):
    rights_dict = {'en': '', 'it': '', 'de': '', 'fr': ''}
    try:
        for locale in LOCALES:
            value_locale = \
                node.xpath('.//gmd:textGroup/gmd:LocalisedCharacterString[@locale="#{}"]'  # noqa
                           .format(locale) + '/text()',
                           namespaces=gmd_namespaces)
            if value_locale:
                rights_dict[locale.lower()] = _clean_string(value_locale[0])
        return rights_dict
    except:
        return ''


def xpath_get_one_value_from_geocat_multilanguage_node(node):
    value = node.xpath('.//gco:CharacterString/text()',
                       namespaces=gmd_namespaces)
    if value:
        return value
    for locale in LOCALES:
        value_locale = \
            node.xpath('.//gmd:textGroup/gmd:LocalisedCharacterString[@locale="#{}"]'  # noqa
                       .format(locale) + '/text()',
                       namespaces=gmd_namespaces)
        if value_locale:
            return value_locale


def xpath_get_url_with_label(node):
    url = xpath_get_url_from_node(node)
    url = {'url': url, 'label': url}
    text_node = node.xpath(GMD_URL_LABEL,
                           namespaces=gmd_namespaces)
    if text_node:
        url_text_node = \
            xpath_get_one_value_from_geocat_multilanguage_node(text_node[0])
        if url_text_node:
            url['label'] = url_text_node[0]
    return url


def xpath_get_url_from_node(node):
    url_node = node.xpath('.//gmd:linkage/gmd:URL/text()',
                          namespaces=gmd_namespaces)
    if url_node:
        return url_node[0]
    for locale in LOCALES:
        url_node = node.xpath('.//che:LocalisedURL[@locale="#{}"]'
                              .format(locale) + '/text()',
                              namespaces=gmd_namespaces)
        if url_node:
            return url_node[0]
    url_node = node.xpath('.//che:LocalisedURL/text()',
                          namespaces=gmd_namespaces)
    if url_node:
        return url_node[0]
    return None


def xpath_get_distribution_from_distribution_node(
        resource_node, protocol):
    """
    sets the geocat distribution: it is later mapped to a ckan
    resource:

    - the normed protocol is determined from the protocol
    - both protocols are stored
    - url and language are determined from the url: a geocat resource
      has just one url. whether it is mapped as access url is decided later
      and depends on the protocol
    - the format and media_type also both depend on the protocol

    There are the following normed protocol types:

    Download Protocol:
    - format and media type are derived from the format,
      that is passed as a string following the protocol name:
      WWW.DOWNLOAD:INTERLIS, means format and
      media type are set to INTERLIS
    - if the format cannot be drived the media type is set to blank

    Service Resource:
    - the format is derived from the protocol: OGC:WMS has format WMS
    - the media type is not set

    Map Preview Resources, Linked Data :
    - these resources don't have a format
    """
    distribution = {}

    name_node = xpath_get_single_sub_node_for_node_and_path(
        node=resource_node, path=GMD_RESOURCE_NAME)
    if name_node:
        distribution['name'] = \
            xpath_get_language_dict_from_geocat_multilanguage_node(
                name_node)
    else:
        distribution['name'] = {'en': '', 'it': '', 'de': '', 'fr': ''}
    description_node = \
        xpath_get_single_sub_node_for_node_and_path(
            node=resource_node, path=GMD_RESOURCE_DESCRIPTION)
    if description_node is not None:
        distribution['description'] = \
            xpath_get_language_dict_from_geocat_multilanguage_node(
                description_node)
    else:
        distribution['description'] = {'en': '', 'it': '', 'de': '', 'fr': ''}

    normed_protocol = _get_normed_protocol(protocol)
    distribution['protocol'] = protocol
    distribution['normed_protocol'] = normed_protocol

    _set_distribution_format_and_media_type(
        protocol,
        normed_protocol,
        distribution
    )

    GMD_URL = './/gmd:linkage'
    url_node = \
        xpath_get_single_sub_node_for_node_and_path(
            node=resource_node, path=GMD_URL)
    if url_node is not None:
        distribution_url, distribution_language = \
            xpath_get_url_and_languages(url_node)
        distribution['url'] = _clean_string(distribution_url)
        distribution['language'] = distribution_language
    return distribution


def _set_distribution_format_and_media_type(
    protocol,
    normed_protocol,
    distribution,
):
    protocol_is_download_protocol_and_has_format = \
        normed_protocol == DOWNLOAD_PROTOCOL and \
        protocol.startswith(DOWNLOAD_PROTOCOL + ':')
    if protocol_is_download_protocol_and_has_format:
        format = protocol.replace(DOWNLOAD_PROTOCOL + ':', '')
        if format:
            distribution['media_type'] = format
            distribution['format'] = format
        else:
            distribution['media_type'] = ""
    elif normed_protocol == DOWNLOAD_PROTOCOL:
        distribution['media_type'] = ""
    elif normed_protocol in LINKED_DATA_PROTOCOL:
        format = re.findall(r'([^:]+$)', protocol)[0]
        distribution['format'] = format
    elif normed_protocol == ESRI_REST_PROTOCOL:
        distribution['format'] = API_FORMAT
    elif normed_protocol == APP_PROTOCOL:
        distribution['format'] = SERVICE_FORMAT
    elif normed_protocol == MAP_PROTOCOL:
        distribution['format'] = SERVICE_FORMAT
    elif normed_protocol in FORMATED_SERVICE_PROTOCOLS:
        format = re.findall(r'(?<=:).*$', normed_protocol)[0]
        distribution['format'] = format


def xpath_get_geocat_services(node):
    service_nodes = \
        xpath_get_all_sub_nodes_for_node_and_path(
            node=node, path=GMD_SERVICE_NODES)
    geocat_services = []
    if service_nodes:
        for service_node in service_nodes:
            geocat_service = {}
            geocat_service['name'] = xpath_get_single_sub_node_for_node_and_path(  # noqa
                node=service_node, path=GMD_SERVICE_TITLE)
            geocat_service['url'], _ = \
                xpath_get_first_of_values_from_path_list(
                    node=service_node, path_list=GMD_SERVICE_URLS
                )
            geocat_service['media_type'] = xpath_get_single_sub_node_for_node_and_path(  # noqa
                node=service_node, path=GMD_MEDIA_TYPE)
            geocat_services.append(geocat_service)
    return geocat_services


def _get_normed_protocol(protocol):
    if protocol != APP_PROTOCOL:
        normed_protocol = [normed_protocol
                           for normed_protocol in NORMED_PROTOCOLS
                           if protocol.startswith(normed_protocol)]
        if normed_protocol:
            return normed_protocol[0]
    if protocol == APP_PROTOCOL:
        return APP_PROTOCOL
    log.error(
        "unknown protocol detected: {}. Could not be mapped to normed protocol"
        .format(protocol)
    )
    return None


def _clean_string(value):
    try:
        return re.sub('\s+', ' ', value).strip()
    except TypeError:
        return value


class MetadataFormatError(Exception):
    pass
