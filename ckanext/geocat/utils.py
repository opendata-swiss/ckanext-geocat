import ckan.plugins.toolkit as tk
from ckan import model
from ckan.model import Session


def find_existing_package(dataset_identifier):
    package_show_context = {'model': model, 'session': Session,
                            'ignore_auth': True}

    user = tk.get_action('get_site_user')({'ignore_auth': True}, {})
    package_show_context.update({'user': user['name']})

    param = 'identifier:%s' % dataset_identifier
    result = tk.get_action('package_search')(package_show_context,
                                             {'fq': param})
    try:
        return result['results'][0]
    except (KeyError, IndexError, TypeError):
        raise tk.ObjectNotFound
