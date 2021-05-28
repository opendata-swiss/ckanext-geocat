import ckan.plugins.toolkit as tk
from ckan import model
from ckan.model import Session

DEFAULT_CONTEXT = {
        'model': model,
        'session': Session,
        'ignore_auth': True
    }


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


def _get_default_context():
    return {
        'model': model,
        'session': Session,
        'ignore_auth': True
    }
