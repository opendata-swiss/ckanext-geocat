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


class GeoMetadataMapping(object):

    def __init__(self, organization_slug, geocat_perma_link, geocat_perma_label):  # noqa
        self.geocat_perma_link = geocat_perma_link
        self.geocat_perma_label = geocat_perma_label
        self.organization_slug = organization_slug

    def get_metadata(self, csw_record_as_string, geocat_id):
        root_node = xpath_utils.get_elem_tree_from_string(csw_record_as_string)
        dataset_dict = {}
        dataset_dict['identifier'] = \
            _map_dataset_identifier(
                node=root_node,
                organization_slug=self.organization_slug)
        dataset_dict['title'] = \
            _map_dataset_title(node=root_node)
        dataset_dict['decription'] = \
            _map_dataset_description(node=root_node)
        dataset_dict['publishers'] = \
            _map_dataset_publisher(node=root_node)
        dataset_dict['contact_points'] = \
            _map_dataset_contact_points(node=root_node)
        dataset_dict['issued'] = \
            _map_dataset_issued(node=root_node)
        dataset_dict['modified'] = \
            _map_dataset_modified(node=root_node)
        dataset_dict['keywords'] = \
            _map_dataset_keywords(node=root_node)
        dataset_dict['groups'] = \
            _map_dataset_categories(node=root_node)
        dataset_dict['accrual_periodicity'] = _map_dataset_frequency(node=root_node)
        dataset_dict['coverage'] = \
            _map_dataset_coverage()
        dataset_dict['spatial'] = \
            _map_dataset_spatial(node=root_node)
        dataset_dict['owner_org'] = self.organization_slug
        return dataset_dict


def _map_dataset_identifier(node, organization_slug):
    GMD_IDENTIFIER = './/gmd:fileIdentifier/gco:CharacterString/text()'
    geocat_identifier = xpath_utils.xpath_get_single_sub_node_for_node_and_path(node=node, path=GMD_IDENTIFIER)  # noqa
    if geocat_identifier:
        return ogdch_map_utils.map_geocat_to_ogdch_identifier(geocat_identifier, organization_slug)  # noqa


def _map_dataset_title(node):
    GMD_TITLE = '//gmd:identificationInfo//gmd:citation//gmd:title'
    title_node = xpath_utils.xpath_get_single_sub_node_for_node_and_path(node=node, path=GMD_TITLE)  # noqa
    if len(title_node):
        return xpath_utils.xpath_get_language_dict_from_geocat_multilanguage_node(title_node)  # noqa


def _map_dataset_description(node):
    GMD_DESCRIPTION = '//gmd:identificationInfo//gmd:abstract'
    description_node = xpath_utils.xpath_get_single_sub_node_for_node_and_path(node=node, path=GMD_DESCRIPTION)  # noqa
    if len(description_node):
        return xpath_utils.xpath_get_language_dict_from_geocat_multilanguage_node(description_node)  # noqa


def _map_dataset_publisher(node):
    GMD_PUBLISHER = [
        '//gmd:identificationInfo//gmd:pointOfContact[.//gmd:CI_RoleCode/@codeListValue = "publisher"]//gmd:organisationName',  # noqa
        '//gmd:identificationInfo//gmd:pointOfContact[.//gmd:CI_RoleCode/@codeListValue = "owner"]//gmd:organisationName',  # noqa
        '//gmd:identificationInfo//gmd:pointOfContact[.//gmd:CI_RoleCode/@codeListValue = "pointOfContact"]//gmd:organisationName',  # noqa
        '//gmd:identificationInfo//gmd:pointOfContact[.//gmd:CI_RoleCode/@codeListValue = "distributor"]//gmd:organisationName',  # noqa
        '//gmd:identificationInfo//gmd:pointOfContact[.//gmd:CI_RoleCode/@codeListValue = "custodian"]//gmd:organisationName',  # noqa
        '//gmd:contact//che:CHE_CI_ResponsibleParty//gmd:organisationName/gco:CharacterString',  # noqa
    ]
    publisher_node = xpath_utils.xpath_get_first_of_values_from_path_list(node=node, path_list=GMD_PUBLISHER, get=xpath_utils.XPATH_NODE)  # noqa
    if len(publisher_node):
        geocat_publisher = xpath_utils.xpath_get_one_value_from_geocat_multilanguage_node(publisher_node)  # noqa
        if geocat_publisher:
            return ogdch_map_utils.map_to_ogdch_publishers(geocat_publisher)
    EMPTY_PUBLISHER = [{'label': ''}]
    return EMPTY_PUBLISHER


def _map_dataset_contact_points(node):
    GMD_CONTACT_POINT = [
        '//gmd:identificationInfo//gmd:pointOfContact[.//gmd:CI_RoleCode/@codeListValue = "pointOfContact"]//gmd:address//gmd:electronicMailAddress/gco:CharacterString',  # noqa
        '//gmd:identificationInfo//gmd:pointOfContact[.//gmd:CI_RoleCode/@codeListValue = "owner"]//gmd:address//gmd:electronicMailAddress/gco:CharacterString',  # noqa
        '//gmd:identificationInfo//gmd:pointOfContact[.//gmd:CI_RoleCode/@codeListValue = "publisher"]//gmd:address//gmd:electronicMailAddress/gco:CharacterString',  # noqa
        '//gmd:identificationInfo//gmd:pointOfContact[.//gmd:CI_RoleCode/@codeListValue = "distributor"]//gmd:address//gmd:electronicMailAddress/gco:CharacterString',  # noqa
        '//gmd:identificationInfo//gmd:pointOfContact[.//gmd:CI_RoleCode/@codeListValue = "custodian"]//gmd:address//gmd:electronicMailAddress/gco:CharacterString',  # noqa
        '//gmd:contact//che:CHE_CI_ResponsibleParty//gmd:address//gmd:electronicMailAddress/gco:CharacterString',  # noqa
    ]
    geocat_contact_point = xpath_utils.xpath_get_first_of_values_from_path_list(node=node, path_list=GMD_CONTACT_POINT, get=xpath_utils.XPATH_TEXT)  # noqa
    if geocat_contact_point:
        return ogdch_map_utils.map_contact_points(geocat_contact_point)  # noqa
    EMPTY_CONTACT_POINTS = []
    return EMPTY_CONTACT_POINTS


def _map_dataset_issued(node):
    GMD_ISSUED = [
        '//gmd:identificationInfo//gmd:citation//gmd:CI_Date[.//gmd:CI_DateTypeCode/@codeListValue = "publication"]//gco:DateTime',  # noqa
        '//gmd:identificationInfo//gmd:citation//gmd:CI_Date[.//gmd:CI_DateTypeCode/@codeListValue = "publication"]//gco:Date',  # noqa
        '//gmd:identificationInfo//gmd:citation//gmd:CI_Date[.//gmd:CI_DateTypeCode/@codeListValue = "creation"]//gco:DateTime',  # noqa
        '//gmd:identificationInfo//gmd:citation//gmd:CI_Date[.//gmd:CI_DateTypeCode/@codeListValue = "creation"]//gco:Date',  # noqa
        '//gmd:identificationInfo//gmd:citation//gmd:CI_Date[.//gmd:CI_DateTypeCode/@codeListValue = "revision"]//gco:DateTime',  # noqa
        '//gmd:identificationInfo//gmd:citation//gmd:CI_Date[.//gmd:CI_DateTypeCode/@codeListValue = "revision"]//gco:Date',  # noqa
        ]
    geocat_issued = xpath_utils.xpath_get_first_of_values_from_path_list(node=node, path_list=GMD_ISSUED, get=xpath_utils.XPATH_TEXT)  # noqa
    if geocat_issued:
        return ogdch_map_utils.map_to_ogdch_datetime(geocat_issued)
    ISSUED_EMPTY = ''
    return ISSUED_EMPTY


def _map_dataset_modified(node):
    GMD_MODIFIED = [
        '//gmd:identificationInfo//gmd:citation//gmd:CI_Date[.//gmd:CI_DateTypeCode/@codeListValue = "revision"]//gco:DateTime',  # noqa
        '//gmd:identificationInfo//gmd:citation//gmd:CI_Date[.//gmd:CI_DateTypeCode/@codeListValue = "revision"]//gco:Date',  # noqa
    ]
    geocat_modified = xpath_utils.xpath_get_first_of_values_from_path_list(node=node, path_list=GMD_MODIFIED, get=xpath_utils.XPATH_TEXT)  # noqa
    if geocat_modified:
        return ogdch_map_utils.map_to_ogdch_datetime(geocat_modified)  # noqa
    MODIFIED_EMPTY = ''
    return MODIFIED_EMPTY


def _map_dataset_keywords(node):
    GMD_KEYWORDS = '//gmd:identificationInfo//gmd:descriptiveKeywords//gmd:keyword'  # noqa
    keyword_nodes = node.xpath(GMD_KEYWORDS, namespaces=gmd_namespaces)  # noqa
    geocat_keywords = []
    for node in keyword_nodes:
        keyword_dict = xpath_utils.xpath_get_language_dict_from_geocat_multilanguage_node(node)  # noqa
        geocat_keywords.append(keyword_dict)
    if geocat_keywords:
        return ogdch_map_utils.map_to_ogdch_keywords(geocat_keywords)
    KEYWORDS_EMPTY = []
    return KEYWORDS_EMPTY


def _map_dataset_categories(node):
    GMD_THEME = '//gmd:identificationInfo//gmd:topicCategory/gmd:MD_TopicCategoryCode/text()'  # noqa
    geocat_categories = xpath_utils.xpath_get_all_sub_nodes_for_node_and_path(node=node, path=GMD_THEME)  # noqa
    if geocat_categories:
        return ogdch_map_utils.map_to_ogdch_categories(geocat_categories)
    CATEGORIES_EMPTY = []
    return CATEGORIES_EMPTY


def _map_dataset_frequency(node):
    GMD_ACRUAL_PERIDICITY = '//gmd:identificationInfo//che:CHE_MD_MaintenanceInformation/gmd:maintenanceAndUpdateFrequency/gmd:MD_MaintenanceFrequencyCode/@codeListValue'  # noqa
    geocat_frequency = xpath_utils.xpath_get_single_sub_node_for_node_and_path(node=node, path=GMD_ACRUAL_PERIDICITY)  # noqa
    if geocat_frequency:
        accrual_periodicity = ogdch_map_utils.map_frequency(geocat_frequency)
        if accrual_periodicity:
            return accrual_periodicity
    FREQUENCY_EMPTY = ''
    return FREQUENCY_EMPTY


def _map_dataset_coverage():
    COVERAGE_NOT_IMPLEMENTED = ''
    return COVERAGE_NOT_IMPLEMENTED


def _map_dataset_spatial(node):
    GMD_SPATIAL = '//gmd:identificationInfo//gmd:extent//gmd:description/gco:CharacterString/text()'  # noqa
    geocat_spatial = xpath_utils.xpath_get_single_sub_node_for_node_and_path(node=node, path=GMD_SPATIAL)  # noqa
    if geocat_spatial:
        return geocat_spatial
    SPACIAL_EMPTY = ''
    return SPACIAL_EMPTY
