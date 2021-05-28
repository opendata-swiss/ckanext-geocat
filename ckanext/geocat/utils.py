from collections import namedtuple
import ckan.plugins.toolkit as tk
from ckan import model
from ckan.model import Session

OgdchDatasetInfo = namedtuple('OgdchDatasetInfo', ['name', 'belongs_to_harvester', 'package_id'])  # noqa


def find_existing_package(dataset_identifier):
    context = _get_default_context()
    user = tk.get_action('get_site_user')({'ignore_auth': True}, {})
    context.update({'user': user['name']})
    param = 'identifier:%s' % dataset_identifier
    result = tk.get_action('package_search')(context, {'fq': param})  # noqa
    try:
        return result['results'][0]
    except (KeyError, IndexError, TypeError):
        raise tk.ObjectNotFound


def get_organization_slug_for_harvest_source(harvest_source_id):
    context = _get_default_context()
    try:
        source_dataset = tk.get_action('package_show')(context, {'id': harvest_source_id})  # noqa
        return source_dataset.get('organization').get('name')
    except (KeyError, IndexError, TypeError):
        raise tk.ObjectNotFound


def get_packages_to_delete(organization_name, harvest_source_id, gathered_ogdch_identifiers):  # noqa
    existing_dataset_infos = get_dataset_infos_for_organization(
        organization_name=organization_name,
        harvest_source_id=harvest_source_id
    )
    return [(identifier, info) for identifier, info in existing_dataset_infos.items()    # noqa
            if info.belongs_to_harvester and identifier not in gathered_ogdch_identifiers]    # noqa


def get_dataset_infos_for_organization(organization_name, harvest_source_id):
    context = _get_default_context()
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
            result = tk.get_action('package_search')(context,
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
                    dataset_harvest_source_id = get_value_from_dataset_extras(extras, 'harvest_source_id')  # noqa
                    if dataset_harvest_source_id and dataset_harvest_source_id == harvest_source_id:  # noqa
                        belongs_to_harvester = True
                    else:
                        belongs_to_harvester = False
                    ogdch_dataset_infos[dataset['identifier']] = OgdchDatasetInfo(  # noqa
                        name=dataset['name'],
                        package_id=dataset['id'],
                        belongs_to_harvester=belongs_to_harvester)
            processed_count += len(datasets_in_result)
        except Exception as e:
            print("Error occured while searching for packages with fq: {}, error: {}".format(fq, e))  # noqa
            break
    return ogdch_dataset_infos


def map_geocat_to_ogdch_identifier(geocat_identifier, organization_slug):
    return '@'.join([geocat_identifier, organization_slug])


def _get_default_context():
    return {
        'model': model,
        'session': Session,
        'ignore_auth': True
    }


def get_value_from_dataset_extras(extras, key):
    if extras:
        extras_reduced_to_key = [item.get('value') for item in extras if item.get('key') == key]  # noqa
        if extras_reduced_to_key:
            return extras_reduced_to_key[0]
    return None
