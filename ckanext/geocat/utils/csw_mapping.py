# -*- coding: utf-8 -*-

from rdflib import Literal
from ckanext.geocat.utils import ogdch_map_utils, xpath_utils, vocabulary_utils  # noqa
from ckanext.geocat.utils.vocabulary_utils import SKOS

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

    def __init__(self, organization_slug, geocat_perma_link, geocat_perma_label,  # noqa
                 legal_basis_url, valid_identifiers):  # noqa
        self.geocat_perma_link = geocat_perma_link
        self.geocat_perma_label = geocat_perma_label
        self.organization_slug = organization_slug
        self.legal_basis_url = legal_basis_url
        self.valid_identifiers = valid_identifiers
        self.terms_of_use_graph = vocabulary_utils.get_terms_of_use()

    def get_metadata(self, csw_record_as_string, geocat_id):
        root_node = xpath_utils.get_elem_tree_from_string(csw_record_as_string)
        dataset_dict = {}
        dataset_dict['identifier'] = \
            _map_dataset_identifier(
                node=root_node,
                organization_slug=self.organization_slug)
        dataset_dict['title'] = _map_dataset_title(node=root_node)
        dataset_dict['description'] = _map_dataset_description(node=root_node)
        dataset_dict['publishers'] = _map_dataset_publisher(node=root_node)
        dataset_dict['contact_points'] = _map_dataset_contact_points(node=root_node)  # noqa
        dataset_dict['issued'] = _map_dataset_issued(node=root_node)
        dataset_dict['modified'] = _map_dataset_modified(node=root_node)
        dataset_dict['keywords'] = _map_dataset_keywords(node=root_node)
        dataset_dict['groups'] = _map_dataset_categories(node=root_node)
        dataset_dict['language'] = _map_dataset_language(node=root_node)
        dataset_dict['accrual_periodicity'] = _map_dataset_frequency(node=root_node)  # noqa
        dataset_dict['coverage'] = _map_dataset_coverage()
        dataset_dict['spatial'] = _map_dataset_spatial(node=root_node)
        dataset_dict['temporals'] = _map_dataset_temporals(node=root_node)
        dataset_dict['see_alsos'] = \
            _map_dataset_see_alsos(node=root_node,
                                   organization_slug=self.organization_slug,
                                   valid_identifiers=self.valid_identifiers)
        dataset_dict['owner_org'] = self.organization_slug
        rights = _map_dataset_rights(node=root_node, terms_of_use=self.terms_of_use_graph)  # noqa

        dataset_dict['relations'] = []
        dataset_dict['resources'] = []
        download_formats = _get_download_distribution_formats(node=root_node)
        service_formats = _get_service_distribution_formats(node=root_node)
        GMD_PROTOCOL = './/gmd:protocol/gco:CharacterString/text()'
        GMD_RESOURCES = '//gmd:distributionInfo/gmd:MD_Distribution//gmd:transferOptions//gmd:CI_OnlineResource'  # noqa
        landing_page_protocols = ogdch_map_utils.get_landing_page_protocols()
        relation_protocols = ogdch_map_utils.get_relation_protocols()

        resource_nodes = xpath_utils.xpath_get_all_sub_nodes_for_node_and_path(node=root_node, path=GMD_RESOURCES)  # noqa
        if resource_nodes is not None:
            for resource_node in resource_nodes:
                protocol = xpath_utils.xpath_get_single_sub_node_for_node_and_path(node=resource_node, path=GMD_PROTOCOL)  # noqa
                if protocol in relation_protocols:
                    if not dataset_dict.get('url') and protocol in landing_page_protocols:  # noqa
                        dataset_dict['url'] = xpath_utils.xpath_get_url_with_label_from_distribution(resource_node).get('url')  # noqa
                    else:
                        url_with_label = xpath_utils.xpath_get_url_with_label_from_distribution(resource_node)  # noqa
                        if url_with_label:
                            dataset_dict['relations'].append(url_with_label)
                else:
                    geocat_resource = \
                        xpath_utils.xpath_get_distribution_from_distribution_node(  # noqa
                            resource_node=resource_node,
                            protocol=protocol,
                            download_formats=download_formats,
                            service_formats=service_formats,
                        )
                    resource = ogdch_map_utils.map_resource(
                        geocat_resource=geocat_resource,
                        issued=dataset_dict['issued'],
                        modified=dataset_dict['modified'],
                        rights=rights,
                    )
                    dataset_dict['resources'].append(resource)

        dataset_dict['relations'].append(ogdch_map_utils.get_permalink(
            geocat_id=geocat_id,
            geocat_perma_link=self.geocat_perma_link,
            geocat_perma_label=self.geocat_perma_label,
        ))
        if self.legal_basis_url:
            dataset_dict['relations'].append(ogdch_map_utils.get_legal_basis_link(  # noqa
                legal_basis_url=self.legal_basis_url,
            ))
        return dataset_dict


def _map_dataset_identifier(node, organization_slug):
    GMD_IDENTIFIER = './/gmd:fileIdentifier/gco:CharacterString/text()'
    geocat_identifier = xpath_utils.xpath_get_single_sub_node_for_node_and_path(node=node, path=GMD_IDENTIFIER)  # noqa
    if geocat_identifier:
        return ogdch_map_utils.map_geocat_to_ogdch_identifier(geocat_identifier, organization_slug)  # noqa


def _map_dataset_title(node):
    GMD_TITLE = '//gmd:identificationInfo//gmd:citation//gmd:title'
    title_node = xpath_utils.xpath_get_single_sub_node_for_node_and_path(node=node, path=GMD_TITLE)  # noqa
    if title_node is not None:
        return xpath_utils.xpath_get_language_dict_from_geocat_multilanguage_node(title_node)  # noqa
    return {'en': '', 'it': '', 'de': '', 'fr': ''}


def _map_dataset_description(node):
    import pdb; pdb.set_trace()
    GMD_DESCRIPTION = '//gmd:identificationInfo//gmd:abstract'
    description_node = xpath_utils.xpath_get_single_sub_node_for_node_and_path(node=node, path=GMD_DESCRIPTION)  # noqa
    if description_node is not None:
        return xpath_utils.xpath_get_language_dict_from_geocat_multilanguage_node(description_node)  # noqa
    return {'en': '', 'it': '', 'de': '', 'fr': ''}


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
    if publisher_node is not None:
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


def _map_dataset_language(node):
    GMD_LANGUAGE = ['//gmd:identificationInfo//gmd:language/gco:CharacterString/text()',  # noqa
                    '//gmd:language/gmd:LanguageCode/@codeListValue']
    geocat_languages = xpath_utils.xpath_get_all_values_for_node_and_path_list(node=node, path_list=GMD_LANGUAGE)  # noqa
    languages = []
    if geocat_languages:
        for geocat_language in set(geocat_languages):
            ogdch_language = ogdch_map_utils.map_language(geocat_language)
            if ogdch_language:
                languages.append(ogdch_language)
    return languages


def _get_download_distribution_formats(node):
    GMD_DOWNLOAD_FORMATS = ['//gmd:distributionInfo//gmd:distributionFormat//gmd:name//gco:CharacterString/text()']  # noqa
    return xpath_utils.xpath_get_all_values_for_node_and_path_list(node=node, path_list=GMD_DOWNLOAD_FORMATS)  # noqa


def _get_service_distribution_formats(node):
    GMD_SERVICE_FORMATS = ['//gmd:identificationInfo//srv:serviceType/gco:LocalName/text()']  # noqa
    return xpath_utils.xpath_get_all_values_for_node_and_path_list(node=node, path_list=GMD_SERVICE_FORMATS)  # noqa


def _map_dataset_temporals(node):
    GMD_TEMPORAL_START = '//gmd:identificationInfo//gmd:extent//gmd:temporalElement//gml:TimePeriod/gml:beginPosition/text()'  # noqa
    GMD_TEMPORAL_END = '//gmd:identificationInfo//gmd:extent//gmd:temporalElement//gml:TimePeriod/gml:endPosition/text()'  # noqa
    geocat_temporal_start = xpath_utils.xpath_get_single_sub_node_for_node_and_path(node=node, path=GMD_TEMPORAL_START)  # noqa
    geocat_temporal_end = xpath_utils.xpath_get_single_sub_node_for_node_and_path(node=node, path=GMD_TEMPORAL_END)  # noqa
    return ogdch_map_utils.map_temporals(geocat_temporal_start, geocat_temporal_end)  # noqa


def _map_dataset_see_alsos(node, organization_slug, valid_identifiers):
    GMD_SEE_ALSOS = '//gmd:identificationInfo//gmd:aggregationInfo//gmd:aggregateDataSetIdentifier/gmd:MD_Identifier/gmd:code/gco:CharacterString/text()'  # noqa
    geocat_see_alsos = xpath_utils.xpath_get_all_sub_nodes_for_node_and_path(node=node, path=GMD_SEE_ALSOS)  # noqa
    if geocat_see_alsos:
        return ogdch_map_utils.map_see_alsos(geocat_see_alsos, organization_slug, valid_identifiers)  # noqa
    return []


def _map_dataset_rights(node, terms_of_use):
    GMD_RIGHTS = './/gmd:resourceConstraints//gmd:otherConstraints'
    rights_node = xpath_utils.xpath_get_single_sub_node_for_node_and_path(node=node, path=GMD_RIGHTS)  # noqa
    if rights_node is not None:
        geocat_rights_dict = xpath_utils.xpath_get_rights_dict_form_rights_node(rights_node)  # noqa
        if geocat_rights_dict:
            for lang, rights_value in geocat_rights_dict.items():
                rights_literal = Literal(rights_value, lang=lang)
                for rights_uri in terms_of_use.subjects(object=rights_literal):
                    for mapping_object in terms_of_use.objects(predicate=SKOS.mappingRelation, subject=rights_uri):  # noqa
                        ogdch_rights = str(mapping_object)
                        return ogdch_rights
    DEFAULT_RIGHTS = 'NonCommercialNotAllowed-CommercialNotAllowed-ReferenceRequired'  # noqa
    return DEFAULT_RIGHTS
