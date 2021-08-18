# -*- coding: utf-8 -*-

from rdflib import Literal
from ckanext.geocat.utils import ogdch_map_utils, xpath_utils, vocabulary_utils  # noqa
from ckanext.geocat.utils.vocabulary_utils import SKOS

import logging
log = logging.getLogger(__name__)

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
GMD_PROTOCOL = './/gmd:protocol/gco:CharacterString/text()'
GMD_RESOURCES = '//gmd:distributionInfo/gmd:MD_Distribution//gmd:transferOptions//gmd:CI_OnlineResource'  # noqa
GMD_IDENTIFIER = './/gmd:fileIdentifier/gco:CharacterString/text()'
GMD_TITLE = '//gmd:identificationInfo//gmd:citation//gmd:title'
GMD_ISSUED = [
    '//gmd:identificationInfo//gmd:citation//gmd:CI_Date[.//gmd:CI_DateTypeCode/@codeListValue = "publication"]//gco:DateTime',  # noqa
    '//gmd:identificationInfo//gmd:citation//gmd:CI_Date[.//gmd:CI_DateTypeCode/@codeListValue = "publication"]//gco:Date',  # noqa
    '//gmd:identificationInfo//gmd:citation//gmd:CI_Date[.//gmd:CI_DateTypeCode/@codeListValue = "creation"]//gco:DateTime',  # noqa
    '//gmd:identificationInfo//gmd:citation//gmd:CI_Date[.//gmd:CI_DateTypeCode/@codeListValue = "creation"]//gco:Date',  # noqa
    '//gmd:identificationInfo//gmd:citation//gmd:CI_Date[.//gmd:CI_DateTypeCode/@codeListValue = "revision"]//gco:DateTime',  # noqa
    '//gmd:identificationInfo//gmd:citation//gmd:CI_Date[.//gmd:CI_DateTypeCode/@codeListValue = "revision"]//gco:Date',  # noqa
]
GMD_DESCRIPTION = '//gmd:identificationInfo//gmd:abstract'
GMD_RIGHTS = './/gmd:resourceConstraints//gmd:otherConstraints'
GMD_SEE_ALSOS = '//gmd:identificationInfo//gmd:aggregationInfo//gmd:aggregateDataSetIdentifier/gmd:MD_Identifier/gmd:code/gco:CharacterString/text()'  # noqa
GMD_TEMPORAL_START = '//gmd:identificationInfo//gmd:extent//gmd:temporalElement//gml:TimePeriod/gml:beginPosition/text()'  # noqa
GMD_TEMPORAL_END = '//gmd:identificationInfo//gmd:extent//gmd:temporalElement//gml:TimePeriod/gml:endPosition/text()'  # noqa
GMD_LANGUAGE = ['//gmd:identificationInfo//gmd:language/gco:CharacterString/text()',  # noqa
                '//gmd:language/gmd:LanguageCode/@codeListValue']
GMD_SPATIAL = '//gmd:identificationInfo//gmd:extent//gmd:description/gco:CharacterString/text()'  # noqa
GMD_PUBLISHER = [
    '//gmd:identificationInfo//gmd:pointOfContact[.//gmd:CI_RoleCode/@codeListValue = "publisher"]//gmd:organisationName',  # noqa
    '//gmd:identificationInfo//gmd:pointOfContact[.//gmd:CI_RoleCode/@codeListValue = "owner"]//gmd:organisationName',  # noqa
    '//gmd:identificationInfo//gmd:pointOfContact[.//gmd:CI_RoleCode/@codeListValue = "pointOfContact"]//gmd:organisationName',  # noqa
    '//gmd:identificationInfo//gmd:pointOfContact[.//gmd:CI_RoleCode/@codeListValue = "distributor"]//gmd:organisationName',  # noqa
    '//gmd:identificationInfo//gmd:pointOfContact[.//gmd:CI_RoleCode/@codeListValue = "custodian"]//gmd:organisationName',  # noqa
    '//gmd:contact//che:CHE_CI_ResponsibleParty//gmd:organisationName',  # noqa
]
GMD_CONTACT_POINT = [
    '//gmd:identificationInfo//gmd:pointOfContact[.//gmd:CI_RoleCode/@codeListValue = "pointOfContact"]//gmd:address//gmd:electronicMailAddress/gco:CharacterString',  # noqa
    '//gmd:identificationInfo//gmd:pointOfContact[.//gmd:CI_RoleCode/@codeListValue = "owner"]//gmd:address//gmd:electronicMailAddress/gco:CharacterString',  # noqa
    '//gmd:identificationInfo//gmd:pointOfContact[.//gmd:CI_RoleCode/@codeListValue = "publisher"]//gmd:address//gmd:electronicMailAddress/gco:CharacterString',  # noqa
    '//gmd:identificationInfo//gmd:pointOfContact[.//gmd:CI_RoleCode/@codeListValue = "distributor"]//gmd:address//gmd:electronicMailAddress/gco:CharacterString',  # noqa
    '//gmd:identificationInfo//gmd:pointOfContact[.//gmd:CI_RoleCode/@codeListValue = "custodian"]//gmd:address//gmd:electronicMailAddress/gco:CharacterString',  # noqa
    '//gmd:contact//che:CHE_CI_ResponsibleParty//gmd:address//gmd:electronicMailAddress/gco:CharacterString',  # noqa
]
GMD_MODIFIED = [
    '//gmd:identificationInfo//gmd:citation//gmd:CI_Date[.//gmd:CI_DateTypeCode/@codeListValue = "revision"]//gco:DateTime',  # noqa
    '//gmd:identificationInfo//gmd:citation//gmd:CI_Date[.//gmd:CI_DateTypeCode/@codeListValue = "revision"]//gco:Date',  # noqa
]
GMD_KEYWORDS = '//gmd:identificationInfo//gmd:descriptiveKeywords//gmd:keyword'  # noqa
GMD_THEME = '//gmd:identificationInfo//gmd:topicCategory/gmd:MD_TopicCategoryCode/text()'  # noqa
GMD_ACRUAL_PERIDICITY = '//gmd:identificationInfo//che:CHE_MD_MaintenanceInformation/gmd:maintenanceAndUpdateFrequency/gmd:MD_MaintenanceFrequencyCode/@codeListValue'  # noqa

EMPTY_CONTACT_POINTS = []
EMPTY_PUBLISHER = [{'label': ''}]
ISSUED_EMPTY = ''
MODIFIED_EMPTY = ''
KEYWORDS_EMPTY = []
CATEGORIES_EMPTY = []
FREQUENCY_EMPTY = ''
SPACIAL_EMPTY = ''
COVERAGE_NOT_IMPLEMENTED = ''


class GeoMetadataMapping(object):

    def __init__(self,
                 organization_slug,
                 geocat_perma_link,
                 geocat_perma_label,
                 legal_basis_url,
                 default_rights,
                 valid_identifiers):
        self.geocat_perma_link = geocat_perma_link
        self.geocat_perma_label = geocat_perma_label
        self.organization_slug = organization_slug
        self.legal_basis_url = legal_basis_url
        self.valid_identifiers = valid_identifiers
        self.terms_of_use_graph = vocabulary_utils.get_terms_of_use()
        self.default_rights = default_rights

    def get_metadata(self, csw_record_as_string, geocat_id):
        log.debug("processing geocat_id {}".format(geocat_id))
        root_node = xpath_utils.get_elem_tree_from_string(csw_record_as_string)
        dataset_dict = {}
        dataset_dict['identifier'] = \
            _map_dataset_identifier(
                node=root_node,
                organization_slug=self.organization_slug)
        dataset_dict['title'] = _map_dataset_title(node=root_node)
        dataset_dict['description'] = _map_dataset_description(node=root_node)
        dataset_dict['publishers'] = _map_dataset_publisher(node=root_node)
        dataset_dict['contact_points'] = \
            _map_dataset_contact_points(node=root_node)
        dataset_dict['issued'] = _map_dataset_issued(node=root_node)
        dataset_dict['modified'] = _map_dataset_modified(node=root_node)
        dataset_dict['keywords'] = _map_dataset_keywords(node=root_node)
        dataset_dict['groups'] = _map_dataset_categories(node=root_node)
        dataset_dict['language'] = _map_dataset_language(node=root_node)
        dataset_dict['accrual_periodicity'] = \
            _map_dataset_frequency(node=root_node)
        dataset_dict['coverage'] = _map_dataset_coverage()
        dataset_dict['spatial'] = _map_dataset_spatial(node=root_node)
        dataset_dict['temporals'] = _map_dataset_temporals(node=root_node)
        dataset_dict['see_alsos'] = \
            _map_dataset_see_alsos(node=root_node,
                                   organization_slug=self.organization_slug,
                                   valid_identifiers=self.valid_identifiers)
        dataset_dict['owner_org'] = self.organization_slug
        rights = \
            _map_dataset_rights(node=root_node,
                                terms_of_use=self.terms_of_use_graph,
                                default_rights=self.default_rights)

        self.map_resources(dataset_dict, rights, root_node)

        geocat_services = xpath_utils.xpath_get_geocat_services(node=root_node)
        if geocat_services:
            for geocat_service in geocat_services:
                ogdch_service = ogdch_map_utils.map_service(
                                geocat_service=geocat_service,
                                issued=dataset_dict.get('issued', ''),
                                modified=dataset_dict.get('modified', ''),
                                description=dataset_dict['description'],
                                rights=rights,
                            )
                dataset_dict['resources'].append(ogdch_service)
        dataset_dict['relations'].append(ogdch_map_utils.get_permalink(
            geocat_id=geocat_id,
            geocat_perma_link=self.geocat_perma_link,
            geocat_perma_label=self.geocat_perma_label,
        ))
        if self.legal_basis_url:
            dataset_dict['relations'].append(ogdch_map_utils.get_legal_basis_link(  # noqa
                legal_basis_url=self.legal_basis_url,
            ))
        log.debug(dataset_dict)
        return dataset_dict

    def map_resources(self, dataset_dict, rights, root_node):
        dataset_dict['relations'] = []
        dataset_dict['resources'] = []
        landing_page_protocols = ogdch_map_utils.get_landing_page_protocols()
        relation_protocols = ogdch_map_utils.get_relation_protocols()
        resource_nodes = \
            xpath_utils.xpath_get_all_sub_nodes_for_node_and_path(
                node=root_node, path=GMD_RESOURCES)
        if resource_nodes is not None:
            for resource_node in resource_nodes:
                protocol = \
                    xpath_utils.xpath_get_single_sub_node_for_node_and_path(
                        node=resource_node, path=GMD_PROTOCOL)
                if protocol in relation_protocols:
                    if not dataset_dict.get('url') and protocol in landing_page_protocols:  # noqa
                        dataset_dict['url'] = \
                            xpath_utils.xpath_get_url_with_label_from_distribution(  # noqa
                                resource_node).get('url')
                    else:
                        url_with_label = \
                            xpath_utils.xpath_get_url_with_label_from_distribution(  # noqa
                                resource_node)
                        if url_with_label:
                            dataset_dict['relations'].append(url_with_label)
                elif protocol:
                    geocat_resource = \
                        xpath_utils.xpath_get_distribution_from_distribution_node(  # noqa
                            resource_node=resource_node,
                            protocol=protocol,
                        )
                    resource = ogdch_map_utils.map_resource(
                        geocat_resource=geocat_resource,
                        issued=dataset_dict['issued'],
                        modified=dataset_dict['modified'],
                        rights=rights,
                    )
                    dataset_dict['resources'].append(resource)
                    for lang in resource.get('language', []):
                        if lang not in dataset_dict['language']:
                            dataset_dict['language'].append(lang)


def _map_dataset_identifier(node, organization_slug):
    geocat_identifier = \
        xpath_utils.xpath_get_single_sub_node_for_node_and_path(
            node=node, path=GMD_IDENTIFIER)
    if geocat_identifier:
        return ogdch_map_utils.map_geocat_to_ogdch_identifier(
            geocat_identifier, organization_slug)


def _map_dataset_title(node):
    title_node = \
        xpath_utils.xpath_get_single_sub_node_for_node_and_path(
            node=node, path=GMD_TITLE)
    if title_node is not None:
        return xpath_utils.xpath_get_language_dict_from_geocat_multilanguage_node(title_node)  # noqa
    return {'en': '', 'it': '', 'de': '', 'fr': ''}


def _map_dataset_description(node):
    description_node = xpath_utils.xpath_get_single_sub_node_for_node_and_path(
        node=node, path=GMD_DESCRIPTION)
    if description_node is not None:
        return xpath_utils.xpath_get_language_dict_from_geocat_multilanguage_node(description_node)  # noqa
    return {'en': '', 'it': '', 'de': '', 'fr': ''}


def _map_dataset_publisher(node):
    publisher_node = \
        xpath_utils.xpath_get_first_of_values_from_path_list(
            node=node,
            path_list=GMD_PUBLISHER,
            get=xpath_utils.XPATH_NODE)
    if publisher_node is not None:
        geocat_publisher = \
            xpath_utils.xpath_get_one_value_from_geocat_multilanguage_node(publisher_node)  # noqa
        if geocat_publisher:
            return ogdch_map_utils.map_to_ogdch_publishers(geocat_publisher)
    return EMPTY_PUBLISHER


def _map_dataset_contact_points(node):
    geocat_contact_point = \
        xpath_utils.xpath_get_first_of_values_from_path_list(
            node=node,
            path_list=GMD_CONTACT_POINT,
            get=xpath_utils.XPATH_TEXT)
    if geocat_contact_point:
        return ogdch_map_utils.map_contact_points(geocat_contact_point)
    return EMPTY_CONTACT_POINTS


def _map_dataset_issued(node):
    geocat_issued = \
        xpath_utils.xpath_get_first_of_values_from_path_list(
            node=node,
            path_list=GMD_ISSUED,
            get=xpath_utils.XPATH_TEXT)
    if geocat_issued:
        return ogdch_map_utils.map_to_ogdch_datetime(geocat_issued)
    return ISSUED_EMPTY


def _map_dataset_modified(node):
    geocat_modified = xpath_utils.xpath_get_first_of_values_from_path_list(
        node=node, path_list=GMD_MODIFIED, get=xpath_utils.XPATH_TEXT)
    if geocat_modified:
        return ogdch_map_utils.map_to_ogdch_datetime(geocat_modified)
    return MODIFIED_EMPTY


def _map_dataset_keywords(node):
    keyword_nodes = node.xpath(GMD_KEYWORDS, namespaces=gmd_namespaces)
    geocat_keywords = []
    for node in keyword_nodes:
        keyword_dict = \
            xpath_utils.xpath_get_language_dict_from_geocat_multilanguage_node(node)  # noqa
        geocat_keywords.append(keyword_dict)
    if geocat_keywords:
        return ogdch_map_utils.map_to_ogdch_keywords(geocat_keywords)
    return KEYWORDS_EMPTY


def _map_dataset_categories(node):
    geocat_categories = \
        xpath_utils.xpath_get_all_sub_nodes_for_node_and_path(
            node=node,
            path=GMD_THEME)
    if geocat_categories:
        return ogdch_map_utils.map_to_ogdch_categories(geocat_categories)
    return CATEGORIES_EMPTY


def _map_dataset_frequency(node):
    geocat_frequency = \
        xpath_utils.xpath_get_single_sub_node_for_node_and_path(
            node=node,
            path=GMD_ACRUAL_PERIDICITY)
    if geocat_frequency:
        accrual_periodicity = ogdch_map_utils.map_frequency(geocat_frequency)
        if accrual_periodicity:
            return accrual_periodicity
    return FREQUENCY_EMPTY


def _map_dataset_coverage():
    return COVERAGE_NOT_IMPLEMENTED


def _map_dataset_spatial(node):
    geocat_spatial = \
        xpath_utils.xpath_get_single_sub_node_for_node_and_path(
            node=node,
            path=GMD_SPATIAL)
    if geocat_spatial:
        return geocat_spatial
    return SPACIAL_EMPTY


def _map_dataset_language(node):
    geocat_languages = \
        xpath_utils.xpath_get_all_values_for_node_and_path_list(
            node=node,
            path_list=GMD_LANGUAGE)
    languages = []
    if geocat_languages:
        for geocat_language in set(geocat_languages):
            ogdch_language = ogdch_map_utils.map_language(geocat_language)
            if ogdch_language:
                languages.append(ogdch_language)
    return languages


def _map_dataset_temporals(node):
    geocat_temporal_start = \
        xpath_utils.xpath_get_single_sub_node_for_node_and_path(
            node=node,
            path=GMD_TEMPORAL_START)
    geocat_temporal_end = \
        xpath_utils.xpath_get_single_sub_node_for_node_and_path(
            node=node,
            path=GMD_TEMPORAL_END)
    return \
        ogdch_map_utils.map_temporals(
            geocat_temporal_start,
            geocat_temporal_end)


def _map_dataset_see_alsos(node, organization_slug, valid_identifiers):
    geocat_see_alsos = \
        xpath_utils.xpath_get_all_sub_nodes_for_node_and_path(
            node=node,
            path=GMD_SEE_ALSOS)
    if geocat_see_alsos:
        return \
            ogdch_map_utils.map_see_alsos(
                geocat_see_alsos,
                organization_slug,
                valid_identifiers)
    return []


def _map_dataset_rights(node, terms_of_use, default_rights):
    rights_node = \
        xpath_utils.xpath_get_single_sub_node_for_node_and_path(
            node=node,
            path=GMD_RIGHTS)
    if rights_node is not None:
        geocat_rights_dict = \
            xpath_utils.xpath_get_rights_dict_form_rights_node(rights_node)
        if geocat_rights_dict:
            for lang, rights_value in geocat_rights_dict.items():
                rights_literal = Literal(rights_value, lang=lang)
                for rights_uri in terms_of_use.subjects(object=rights_literal):
                    for mapping_object in terms_of_use.objects(predicate=SKOS.mappingRelation, subject=rights_uri):  # noqa
                        ogdch_rights = str(mapping_object)
                        if ogdch_rights:
                            return ogdch_rights
    return default_rights
