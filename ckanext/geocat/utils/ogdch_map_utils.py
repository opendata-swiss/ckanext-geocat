# -*- coding: utf-8 -*-

from datetime import datetime
from ckan.lib.munge import munge_tag
from ckanext.geocat.utils import xpath_utils  # noqa

DEFAULT_RIGHTS = 'NonCommercialNotAllowed-CommercialNotAllowed-ReferenceRequired'  # noqa


def map_geocat_to_ogdch_identifier(geocat_identifier, organization_slug):
    return '@'.join([geocat_identifier, organization_slug])


def map_to_ogdch_publishers(geocat_publisher):
    dataset_publishers = []
    for publisher in geocat_publisher:
        dataset_publishers.append({'label': publisher})
    return dataset_publishers


def map_to_ogdch_datetime(datetime_value):
    try:
        d = datetime.strptime(
            datetime_value[0:len('YYYY-MM-DD')],
            '%Y-%m-%d'
        )
        # we have to calculate this manually since the
        # time library of Python 2.7 does not support
        # years < 1900, see OGD-751 and the time docs
        # https://docs.python.org/2.7/library/time.html
        epoch = datetime(1970, 1, 1)
        return int((d - epoch).total_seconds())
    except (ValueError, KeyError, TypeError, IndexError):
        raise ValueError("Could not parse datetime")


def map_to_ogdch_keywords(geocat_keywords):
    ogdch_keywords = {'fr': [], 'de': [], 'en': [], 'it': []}
    for keyword in geocat_keywords:
        for lang, geocat_keyword in keyword.items():
            if geocat_keyword != 'opendata.swiss' and lang in ['fr', 'de', 'en', 'it']:  # noqa
                ogdch_keywords[lang].append(munge_tag(geocat_keyword))  # noqa
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
        ogdch_groups.extend(theme_mapping.get(category))
    ogdch_groups = set(ogdch_groups)
    return [{'name': group} for group in ogdch_groups]


def map_frequency(geocat_frequency):
    frequency_mapping = {
        'continual': 'http://purl.org/cld/freq/continuous',
        'daily': 'http://purl.org/cld/freq/daily',
        'weekly': 'http://purl.org/cld/freq/weekly',
        'fortnightly': 'http://purl.org/cld/freq/biweekly',
        'monthly': 'http://purl.org/cld/freq/monthly',
        'quarterly': 'http://purl.org/cld/freq/quarterly',
        'biannually': 'http://purl.org/cld/freq/semiannual',
        'annually': 'http://purl.org/cld/freq/annual',
        'asNeeded': 'http://purl.org/cld/freq/completelyIrregular',
        'irregular': 'http://purl.org/cld/freq/completelyIrregular',
    }
    return frequency_mapping.get(geocat_frequency, '')


def map_contact_points(geocat_contact_point):
    contacts = [{'name': geocat_contact_point, 'email': geocat_contact_point}]  # noqa
    return contacts


def map_language(geocat_language):
    language_mapping = {
        'ger': 'de',
        'fra': 'fr',
        'eng': 'en',
        'ita': 'it',
    }
    return language_mapping.get(geocat_language, '')


def map_see_alsos(geocat_see_alsos, organization_slug, valid_identifiers):
    ogdch_see_alsos = [map_geocat_to_ogdch_identifier(geocat_identifier, organization_slug)
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
    return {'url':permalink, 'label': geocat_perma_label}


def get_legal_basis_link(legal_basis_url):
    LEGAL_BASIS_LABEL = 'legal_basis'
    return {'url':legal_basis_url, 'label': LEGAL_BASIS_LABEL}


def map_rights(geocat_rights_dict):
    return DEFAULT_RIGHTS


def get_relation_protocols():
    return ['WWW:LINK-1.0-http--link', 'WWW:LINK', 'CHTOPO:specialised-geoportal']


def get_landing_page_protocols():
    return ['WWW:LINK-1.0-http--link', 'WWW:LINK']


def map_resource(geocat_resource, issued, modified, rights):
    resource_dict = {}
    resource_dict['issued'] = issued
    resource_dict['modified'] = modified
    resource_dict['rights'] = rights
    resource_dict['format'] = geocat_resource.get('format')
    resource_dict['description'] = geocat_resource.get('description')
    resource_dict['media_type'] = geocat_resource.get('format')
    name = geocat_resource.get('name')
    protocol_name = geocat_resource.get('protocol_name')
    if name and protocol_name:
        resource_dict['title'] = protocol_name + " " + name
    elif protocol_name:
        resource_dict['title'] = protocol_name
    else:
        resource_dict['title'] = name
    resource_dict['access_url'] = geocat_resource['url']
    if geocat_resource['protocol'] == xpath_utils.DOWNLOAD_PROTOCOL:
        resource_dict['download_url'] = geocat_resource['url']
    resource_dict['language'] = geocat_resource['language']
    return resource_dict
