# -*- coding: utf-8 -*-

import json
from datetime import datetime
from ckan.lib.munge import munge_tag
from ckanext.geocat.utils import xpath_utils  # noqa
import ckanext.geocat.utils.mapping_utils as mu

ORGANIZATION_URI_BASE = 'https://opendata.swiss/organization/'
MAP_PROTOCOL_PREFIX = "Map (Preview)"


def _get_organization_url(organization_name):
    return ORGANIZATION_URI_BASE + organization_name


def map_geocat_to_ogdch_identifier(geocat_identifier, organization_slug):
    return '@'.join([geocat_identifier, organization_slug])


def map_to_ogdch_publisher(geocat_publisher, organization_slug):
    if not geocat_publisher:
        return
    ogdch_publisher = {
        'name': geocat_publisher.get('name'),
        'url': geocat_publisher.get('url',
                                    _get_organization_url(organization_slug)),
    }
    return json.dumps(ogdch_publisher)


def map_to_ogdch_datetime(datetime_value):
    try:
        d = datetime.strptime(
            datetime_value[0:len('YYYY-MM-DD')],
            '%Y-%m-%d'
        )
        return datetime.isoformat(d)
    except (ValueError, KeyError, TypeError, IndexError):
        raise ValueError("Could not parse datetime")


def map_to_ogdch_keywords(geocat_keywords):
    ogdch_keywords = {'fr': [], 'de': [], 'en': [], 'it': []}
    for keyword in geocat_keywords:
        for lang, geocat_keyword in keyword.items():
            if geocat_keyword != \
                    'opendata.swiss' and lang in ['fr', 'de', 'en', 'it']:
                if geocat_keyword:
                    ogdch_keywords[lang].append(munge_tag(geocat_keyword))
    return ogdch_keywords


def map_to_ogdch_categories(geocat_categories):
    theme_mapping = {
        'imageryBaseMapsEarthCover': ['geography', 'territory'],
        'imageryBaseMapsEarthCover_BaseMaps': ['geography', 'territory'],
        'imageryBaseMapsEarthCover_EarthCover': ['geography', 'territory'],
        'imageryBaseMapsEarthCover_Imagery': ['geography', 'territory'],
        'location': ['geography', 'territory'],
        'elevation': ['geography', 'territory'],
        'boundaries': ['geography', 'territory'],
        'planningCadastre': ['geography', 'territory'],
        'planningCadastre_Planning': ['geography', 'territory'],
        'planningCadastre_Cadastre': ['geography', 'territory'],
        'geoscientificInformation': ['geography', 'territory'],
        'geoscientificInformation_Geology': ['geography', 'territory'],
        'geoscientificInformation_Soils': ['geography', 'territory'],
        'geoscientificInformation_NaturalHazards': ['geography', 'territory'],
        'biota': ['geography', 'territory', 'agriculture'],
        'oceans': ['geography', 'territory'],
        'inlandWaters': ['geography', 'territory'],
        'climatologyMeteorologyAtmosphere': ['geography', 'territory'],
        'environment': ['geography', 'territory'],
        'environment_EnvironmentalProtection': ['geography', 'territory'],
        'environment_NatureProtection': ['geography', 'territory'],
        'society': ['geography', 'culture', 'population'],
        'health': ['geography', 'health'],
        'structure': ['geography', 'construction'],
        'transportation': ['geography', 'mobility'],
        'utilitiesCommunication': ['geography', 'territory', 'energy', 'culture'],  # noqa
        'utilitiesCommunication_Energy': ['geography', 'energy', 'territory'],
        'utilitiesCommunication_Utilities': ['geography', 'territory'],
        'utilitiesCommunication_Communication': ['geography', 'culture'],
        'intelligenceMilitary': ['geography', 'public-order'],
        'farming': ['geography', 'agriculture'],
        'economy': ['geography', 'work', 'national-economy'],
    }
    ogdch_groups = []
    for category in geocat_categories:
        mapped_category = theme_mapping.get(category)
        if mapped_category:
            ogdch_groups.extend(mapped_category)
    ogdch_groups = set(ogdch_groups)
    return [{'name': group} for group in ogdch_groups]


def map_frequency(geocat_frequency):
    frequency_mapping = {
        'continual':
        'http://publications.europa.eu/resource/authority/frequency/CONT',
        'daily':
        'http://publications.europa.eu/resource/authority/frequency/DAILY',
        'weekly':
        'http://publications.europa.eu/resource/authority/frequency/WEEKLY',
        'fortnightly':
        'http://publications.europa.eu/resource/authority/frequency/BIWEEKLY',
        'monthly':
        'http://publications.europa.eu/resource/authority/frequency/MONTHLY',
        'quarterly':
        'http://publications.europa.eu/resource/authority/frequency/QUARTERLY',
        'biannually':
        'http://publications.europa.eu/resource/authority/frequency/ANNUAL_2',
        'annually':
        'http://publications.europa.eu/resource/authority/frequency/ANNUAL',
        'asNeeded':
        'http://publications.europa.eu/resource/authority/frequency/IRREG',
        'irregular':
        'http://publications.europa.eu/resource/authority/frequency/IRREG',
        'notPlanned':
        'http://publications.europa.eu/resource/authority/frequency/NEVER',
        'unknown':
        'http://publications.europa.eu/resource/authority/frequency/UNKNOWN',
    }
    return frequency_mapping.get(geocat_frequency, '')


def map_contact_points(geocat_contact_point):
    contacts = [{'name': geocat_contact_point,
                 'email': geocat_contact_point}]
    return contacts


def map_language(geocat_language):
    language_mapping = {
        'ger': 'de',
        'fre': 'fr',
        'fra': 'fr',
        'eng': 'en',
        'ita': 'it',
    }
    return language_mapping.get(geocat_language, '')


def map_see_alsos(geocat_see_alsos, organization_slug, valid_identifiers):
    ogdch_see_alsos = [
        map_geocat_to_ogdch_identifier(geocat_identifier, organization_slug)
        for geocat_identifier in geocat_see_alsos]
    return [see_also for see_also in ogdch_see_alsos
            if see_also in valid_identifiers]


def map_temporals(geocat_temporal_start, geocat_temporal_end):
    if geocat_temporal_start:
        start_date = map_to_ogdch_datetime(geocat_temporal_start)
        end_date = start_date
        if geocat_temporal_end:
            end_date = map_to_ogdch_datetime(geocat_temporal_end)
        return [{'start_date': start_date,
                 'end_date': end_date}]
    else:
        return []


def get_permalink(geocat_id, geocat_perma_link, geocat_perma_label):
    permalink = geocat_perma_link + geocat_id
    return {'url': permalink, 'label': geocat_perma_label}


def get_legal_basis_link(legal_basis_url):
    LEGAL_BASIS_LABEL = 'legal_basis'
    return {'url': legal_basis_url, 'label': LEGAL_BASIS_LABEL}


def get_landing_page_protocols():
    """If a resource node with one of these protocols has a url, and the
    dataset does not have a url, map the resource node's url onto the dataset.

    If the dataset already has a url, then the url is added to the dataset's
    documentation instead.
    """
    return ['WWW:LINK-1.0-http--link', 'WWW:LINK']


def get_additonal_relation_protocols():
    """If a resource node with one of these protocols has a url, then the url
    is added to the dataset's relations.

    The url from the resource node cannot be mapped as the dataset's url.
    """
    return ['CHTOPO:specialised-geoportal']


def map_resource(geocat_resource, issued, modified, rights):
    """
    map geocat resources to resources on opendata.swiss
    - issued, modified and rights are taken from the dataset
    - the title depends on the normed protocol
    - the format is taken from the geocat resource if it has been set
    - the media type and the download_url are set only for the normed
      protocol WWW:DOWNLOAD
    - url and language are mapped as they come
    - the original protocol is also stored on the resource since
      it helps to trace the resource back to the original geocat resource
    """
    resource_dict = {}
    resource_dict['issued'] = issued
    resource_dict['modified'] = modified
    resource_dict['rights'] = rights
    resource_dict['license'] = rights
    if geocat_resource.get('format'):
        resource_dict['format'] = _map_geocat_resource_format_to_valid_format(
            geocat_resource['format']
        )
    resource_dict['description'] = geocat_resource.get('description')
    resource_dict['title'] = _map_geocat_resource_name_to_title(
        normed_protocol=geocat_resource['normed_protocol'],
        name=geocat_resource.get('name'),
    )
    resource_dict['url'] = _avoid_none_as_value(geocat_resource.get('url'))
    if geocat_resource['normed_protocol'] == xpath_utils.DOWNLOAD_PROTOCOL:
        resource_dict['media_type'] = geocat_resource['media_type']
        resource_dict['download_url'] = geocat_resource['url']
    resource_dict['protocol'] = geocat_resource['protocol']
    resource_dict['language'] = geocat_resource['language']
    return resource_dict


def _avoid_none_as_value(value):
    if not value:
        return ""
    return value


def _map_geocat_resource_name_to_title(normed_protocol, name):
    """
    Only Mpa Preview Resources are prefixed with a protocol
    identifier, so that these resources can be identified by the
    frontend.

    In all other cases the name of the geocat ressurce name is taken as
    resource title.
    """
    if name and normed_protocol == xpath_utils.MAP_PROTOCOL:
        return {
            'de': (MAP_PROTOCOL_PREFIX + " " + name['de']).strip(),
            'fr': (MAP_PROTOCOL_PREFIX + " " + name['fr']).strip(),
            'en': (MAP_PROTOCOL_PREFIX + " " + _remove_duplicate_term_in_name(
                name['en'], "Preview")).strip(),
            'it': (MAP_PROTOCOL_PREFIX + " " + name['it']).strip(),
        }
    return name


def _remove_duplicate_term_in_name(name, term):
    if not name:
        return ""
    return name.lstrip(term)


def map_service(geocat_service, issued, modified, description, rights):
    return {
        'description': description,
        'issued': issued,
        'modified': modified,
        'rights': rights,
        'media_type': geocat_service.get('media_type', ''),
        'url': geocat_service.get('url', '')
    }


def _map_geocat_resource_format_to_valid_format(geocat_format):
    valid_formats = mu.get_format_values()
    for key, value in valid_formats.items():
        if geocat_format == key or geocat_format == key.replace('_', ' '):
            return value
    valid_media_types = mu.get_iana_media_type_values()
    for key, value in valid_media_types.items():
        if geocat_format == key or  geocat_format == key.replace('_', ' '):
            return value
    return geocat_format
