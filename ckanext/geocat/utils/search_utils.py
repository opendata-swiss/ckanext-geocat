from collections import namedtuple
import ckan.plugins.toolkit as tk
from ckan import model
from ckan.model import Session
import json

import logging

log = logging.getLogger(__name__)

OgdchDatasetInfo = namedtuple('OgdchDatasetInfo',
                              ['name', 'belongs_to_harvester', 'package_id'])


def get_organization_slug_for_harvest_source(harvest_source_id):
    context = get_default_context()
    try:
        source_dataset = \
            tk.get_action('package_show')(context, {'id': harvest_source_id})
        return source_dataset.get('organization').get('name')
    except (KeyError, IndexError, TypeError):
        raise tk.ObjectNotFound


def get_packages_to_delete(existing_dataset_infos,
                           gathered_ogdch_identifiers):
    return [
        (identifier, info)
        for identifier, info
        in existing_dataset_infos.items()
        if info.belongs_to_harvester and identifier not in gathered_ogdch_identifiers  # noqa
    ]


def get_double_packages(existing_dataset_infos, gathered_ogdch_identifiers):  # noqa
    return [
        (identifier, info)
        for identifier, info
        in existing_dataset_infos.items()
        if not info.belongs_to_harvester and identifier in gathered_ogdch_identifiers  # noqa
    ]


def find_package_for_identifier(identifier):
    context = get_default_context()
    fq = "identifier:({})".format(identifier)
    try:
        result = tk.get_action('package_search')(context,
                                                 {'fq': fq,
                                                  'include_private': True})
        if result.get('count') > 0:
            pkg = result['results'][0]
            return OgdchDatasetInfo(name=pkg['name'],
                                    package_id=pkg['id'],
                                    belongs_to_harvester=True)
        else:
            return None
    except Exception as e:
        print("Error occured while searching for packages with fq: {}, error: {}"  # noqa
              .format(fq, e))


def get_dataset_infos_for_organization(organization_name, harvest_source_id):
    context = get_default_context()
    rows = 500
    page = 0
    result_count = 0
    fq = "organization:({})".format(organization_name)
    processed_count = 0
    ogdch_dataset_infos = {}
    while page == 0 or processed_count < result_count:
        page = page + 1
        start = (page - 1) * rows
        result = tk.get_action('package_search')(context,
                                                 {'fq': fq,
                                                  'rows': rows,
                                                  'start': start,
                                                  'include_private': True})
        if not result_count:
            result_count = result['count']
        datasets_in_result = result.get('results', [])
        for dataset in datasets_in_result:
            try:
                extras = dataset.get('extras')
                dataset_harvest_source_id = \
                    get_value_from_dataset_extras(extras,
                                                  'harvest_source_id')
                if dataset_harvest_source_id and dataset_harvest_source_id == harvest_source_id:  # noqa
                    belongs_to_harvester = True
                else:
                    belongs_to_harvester = False
                ogdch_dataset_infos[dataset['identifier']] = \
                    OgdchDatasetInfo(
                        name=dataset['name'],
                        package_id=dataset['id'],
                        belongs_to_harvester=belongs_to_harvester)
            except KeyError as e:
                package_id = dataset.get('id') \
                             or dataset.get('name') \
                             or dataset.get('identifier', '')
                log.warn(
                    "KeyError occured while searching with fq {}. "
                    "Package {} is missing field {}"
                    .format(fq, package_id, e)
                )
        processed_count += len(datasets_in_result)
    return ogdch_dataset_infos


def get_default_context():
    return {
        'model': model,
        'session': Session,
        'ignore_auth': True
    }


def get_value_from_dataset_extras(extras, key):
    if extras:
        extras_reduced_to_key = [item.get('value')
                                 for item in extras
                                 if item.get('key') == key]
        if extras_reduced_to_key:
            return extras_reduced_to_key[0]
    return None


def get_value_from_object_extra(harvest_object_extras, key):
    for extra in harvest_object_extras:
        if extra.key == key:
            return extra.value
    return None


def map_resources_to_ids(pkg_dict, pkg_info):
    existing_package = \
        tk.get_action('package_show')({}, {'id': pkg_info.package_id})
    existing_resources = existing_package.get('resources')
    existing_resources_mapping = \
        {r['id']: _get_resource_id_string(r) for r in existing_resources}
    for resource in pkg_dict.get('resources'):
        resource_id_dict = _get_resource_id_string(resource)
        id_to_reuse = [k for k, v in existing_resources_mapping.items()
                       if v == resource_id_dict]
        if id_to_reuse:
            id_to_reuse = id_to_reuse[0]
            resource['id'] = id_to_reuse
            del existing_resources_mapping[id_to_reuse]


def _get_resource_id_string(resource):
    resource_id_dict = {'url': resource.get('url'),
                        'title': resource.get('title'),
                        'description': resource.get('description')}
    return json.dumps(resource_id_dict)
