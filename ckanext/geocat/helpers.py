# -*- coding: utf-8 -*-

from collections import namedtuple
from ckan import model
from ckan.model import Session
import ckan.plugins.toolkit as tk
from ckan.logic import get_action

OgdchDatasetInfo = namedtuple('OgdchDatasetInfo', ['name', 'belongs_to_harvester', 'package_id'])

def get_organization_slug_for_harvest_source(harvest_source_id):
    context = {
        'model': model,
        'session': Session,
        'ignore_auth': True
    }
    source_dataset = get_action('package_show')(context, {'id': harvest_source_id})
    return source_dataset.get('organization').get('name')


def get_dataset_infos_for_organization(organization_name, harvest_source_id):
    context = {
        'model': model,
        'session': Session,
        'ignore_auth': True
    }
    rows = 500
    page = 0
    result_count = 0
    fq = "organization:({})".format(organization_name)
    processed_count = 0
    ogdch_dataset_infos = {}
    while page == 0 or processed_count < result_count:
        try:
            page = page + 1
            start = (page - 1) * rows
            result = get_action('package_search')(context,
                                                {'fq': fq,
                                                 'rows': rows,
                                                 'start': start,
                                                 'include_private': True})
            if not result_count:
                result_count = result['count']
            datasets_in_result = result.get('results')
            if datasets_in_result:
                for dataset in datasets_in_result:
                    extras = dataset.get('extras')
                    dataset_harvest_source_id =  get_value_from_dataset_extras(extras, 'harvest_source_id')
                    if dataset_harvest_source_id and dataset_harvest_source_id == harvest_source_id:
                        belongs_to_harvester = True
                    else:
                        belongs_to_harvester = False
                    ogdch_dataset_infos[dataset['identifier']] = OgdchDatasetInfo(
                        name=dataset['name'],
                        package_id=dataset['id'],
                        belongs_to_harvester=belongs_to_harvester)
            processed_count += len(datasets_in_result)
        except Exception as e:
            print("Error occured while searching for packages with fq: {}, error: {}".format(fq, e))
            break
    return ogdch_dataset_infos


def derive_flat_title(title_dict):
    """localizes language dict if no language is specified"""
    return title_dict.get('de') or title_dict.get('fr') or title_dict.get('en') or title_dict.get('it') or ""


def get_value_from_dataset_extras(extras, key):
    if extras:
        extras_reduced_to_key = [item.get('value') for item in extras if item.get('key') == key]
        if extras_reduced_to_key:
            return extras_reduced_to_key[0]
    return None


def get_value_from_object_extra(harvest_object_extras, key):
    for extra in harvest_object_extras:
        if extra.key == key:
            return extra.value
    return None


