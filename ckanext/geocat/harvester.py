# -*- coding: utf-8 -*-

import traceback

from urlparse import urljoin
from ckan.lib.helpers import json
from ckanext.harvest.model import HarvestObject, HarvestObjectExtra
from ckanext.harvest.harvesters import HarvesterBase
import ckanext.geocat.metadata as md
import ckanext.geocat.xml_loader as loader
from ckan.logic import get_action, NotFound
from ckan.logic.schema import default_update_package_schema,\
    default_create_package_schema
from ckan.lib.navl.validators import ignore
import ckan.plugins.toolkit as tk
from ckan import model
from ckan.model import Session
import uuid

import logging
log = logging.getLogger(__name__)

DEFAULT_PERMA_LINK_URL = 'https://www.geocat.ch/geonetwork/srv/ger/md.viewer#/full_view/'  # noqa
DEFAULT_PERMA_LINK_LABEL = 'geocat.ch Permalink'
DEFAULT_GEOCAT_PROD_ENV = 'https://www.geocat.ch/geonetwork/srv'


class GeocatHarvester(HarvesterBase):
    '''
    The harvester for geocat
    '''

    HARVEST_USER = 'harvest'

    def info(self):
        return {
            'name': 'geocat_harvester',
            'title': 'Geocat harvester',
            'description': (
                'Harvests metadata from geocat (CSW)'
            ),
            'form_config_interface': 'Text'
        }

    def validate_config(self, config):
        if not config:
            return config
        try:
            config_obj = json.loads(config)
            if 'delete_missing_datasets' in config_obj:
                if not isinstance(config_obj['delete_missing_datasets'], bool):
                    raise ValueError('delete_missing_dataset must be boolean')
        except Exception as e:
            raise e
        return config

    def _set_config(self, config_str):
        if config_str:
            self.config = json.loads(config_str)
        else:
            self.config = {}

        if 'user' not in self.config:
            self.config['user'] = self.HARVEST_USER

        if 'delete_missing_datasets' not in self.config:
            self.config['delete_missing_datasets'] = False

        # get config for geocat permalink
        self.config['permalink_url'] = tk.config.get('ckanext.geocat.permalink_url', None) # noqa
        self.config['permalink_bookmark'] = tk.config.get('ckanext.geocat.permalink_bookmark', None) # noqa
        self.config['permalink_title'] = tk.config.get('ckanext.geocat.permalink_title', 'geocat.ch Permalink') # noqa
        self.config['permalink_valid'] = self.config['permalink_url'] and self.config['permalink_bookmark'] # noqa

        log.debug('Using config: %r' % self.config)

    def _find_existing_package(self, package_dict):
        package_show_context = {'model': model, 'session': Session,
                                'ignore_auth': True}

        user = tk.get_action('get_site_user')({'ignore_auth': True}, {})
        package_show_context.update({'user': user['name']})

        param = 'identifier:%s' % package_dict['identifier']
        result = tk.get_action('package_search')(package_show_context,
                                                 {'fq': param})
        try:
            return result['results'][0]
        except (KeyError, IndexError, TypeError):
            raise NotFound

    def gather_stage(self, harvest_job):
        log.debug('In GeocatHarvester gather_stage')

        try:
            self._set_config(harvest_job.source.config)

            if 'organization' not in self.config:
                context = {
                    'model': model,
                    'session': Session,
                    'ignore_auth': True
                }
                source_dataset = get_action('package_show')(
                    context, {'id': harvest_job.source_id})
                self.config['organization'] = source_dataset.get(
                    'organization').get('name')
        except GeocatConfigError as e:
            self._save_gather_error(
                'Config value missing: %s' % str(e),
                harvest_job
            )
            return []

        csw_url = None
        harvest_obj_ids = []
        gathered_dataset_identifiers = []

        try:
            csw_url = harvest_job.source.url.rstrip('/')
            csw = md.CswHelper(url=csw_url)

            cql = self.config.get('cql', None)
            if cql is None:
                cql = "keyword = 'opendata.swiss'"

            log.debug("CQL query: %s" % cql)
            for record_id in csw.get_id_by_search(cql=cql):
                harvest_obj = HarvestObject(
                    guid=record_id,
                    job=harvest_job
                )
                harvest_obj.save()
                harvest_obj_ids.append(harvest_obj.id)
                gathered_dataset_identifiers.append('%s@%s' % (
                    record_id,
                    self.config['organization']
                ))

            log.debug('IDs: %r' % harvest_obj_ids)
        except Exception as e:
            self._save_gather_error(
                'Unable to get content for URL: %s: %s / %s'
                % (csw_url, str(e), traceback.format_exc()),
                harvest_job
            )
            return []

        if self.config['delete_missing_datasets']:
            delete_ids = self._check_for_deleted_datasets(
                harvest_job, gathered_dataset_identifiers
            )
            log.debug('delete_ids: %r' % delete_ids)
            harvest_obj_ids.extend(delete_ids)

        return harvest_obj_ids

    def fetch_stage(self, harvest_object):
        log.debug('In GeocatHarvester fetch_stage')
        self._set_config(harvest_object.job.source.config)

        if not harvest_object:
            log.error('No harvest object received')
            self._save_object_error(
                'No harvest object received',
                harvest_object
            )
            return False

        csw_url = harvest_object.source.url.rstrip('/')
        csw = None
        try:
            csw = md.CswHelper(url=csw_url)
            xml = csw.get_by_id(harvest_object.guid)
            harvest_object.content = xml
            harvest_object.save()
            log.debug('successfully processed ' + harvest_object.guid)
            return True
        except Exception as e:
            response = '-'
            if csw and hasattr(csw.catalog, 'response'):
                response = csw.catalog.response

            self._save_object_error(
                (
                    'Unable to get content for package: %s: %r: %r / %s' %
                    (
                        harvest_object.guid,
                        e,
                        response,
                        traceback.format_exc()
                    )
                ),
                harvest_object
            )
            return False

    def import_stage(self, harvest_object):  # noqa
        log.debug('In GeocatHarvester import_stage')
        self._set_config(harvest_object.job.source.config)

        if not harvest_object:
            log.error('No harvest object received')
            self._save_object_error(
                'No harvest object received',
                harvest_object
            )
            return False

        # check if dataset must be deleted
        import_action = self._get_object_extra(harvest_object, 'import_action')
        if import_action and import_action == 'delete':
            log.debug('import action: %s' % import_action)
            harvest_object.current = False
            return self._delete_dataset({'id': harvest_object.guid})

        try:
            if 'organization' not in self.config:
                context = {
                    'model': model,
                    'session': Session,
                    'ignore_auth': True
                }
                source_dataset = get_action('package_show')(
                    context, {'id': harvest_object.source.id})
                self.config['organization'] = source_dataset.get(
                    'organization').get('name')

            xml_elem = loader.from_string(harvest_object.content)
            dataset_metadata = md.GeocatDcatDatasetMetadata()
            dist_metadata = md.GeocatDcatDistributionMetadata()

            pkg_dict = dataset_metadata.get_metadata(xml_elem)
            dist_list = dist_metadata.get_metadata(xml_elem)

            for dist in dist_list:
                if not dist.get('rights'):
                    dist['rights'] = self.config.get(
                        'rights',
                        'NonCommercialNotAllowed-CommercialNotAllowed-ReferenceRequired'  # noqa
                    )

            geocat_permalink_relation = \
                self._get_geocat_permalink_relation(pkg_dict['identifier'])
            pkg_dict['identifier'] = (
                '%s@%s'
                % (pkg_dict['identifier'], self.config['organization'])
            )

            # geocat returns see_alsos as UUID, check if there are
            # datasets from the same organization as the harvester
            existing_see_alsos = []
            for linked_uuid in pkg_dict['see_alsos']:
                try:
                    identifier = '%s@%s' % (
                        linked_uuid,
                        self.config['organization']
                    )
                    check_dict = {'identifier': identifier}
                    self._find_existing_package(check_dict)
                    existing_see_alsos.append({'dataset_identifier': identifier})  # noqa
                except NotFound:
                    continue
            pkg_dict['see_alsos'] = existing_see_alsos

            pkg_dict['owner_org'] = self.config['organization']
            pkg_dict['resources'] = dist_list
            flat_title = _derive_flat_title(pkg_dict['title'])
            if not flat_title:
                self._save_object_error('Unable to derive name from title %s' % pkg_dict['title'],  # noqa
                                        harvest_object, 'Import')
                return False

            pkg_dict['name'] = self._gen_new_name(flat_title)  # noqa

            # legal basis
            legal_basis_url = self.config.get('legal_basis_url', None)
            if legal_basis_url:
                pkg_dict['relations'].append({
                    'url': legal_basis_url,
                    'label': 'legal_basis'
                })
            if geocat_permalink_relation:
                pkg_dict['relations'].append(geocat_permalink_relation)

            log.debug('package dict: %s' % pkg_dict)

            package_context = {
                'ignore_auth': True,
                'user': self.config['user'],
            }
            try:
                # Change default schema to ignore lists of dicts, which
                # are stored in the '__junk' field
                schema = default_update_package_schema()
                schema['__junk'] = [ignore]

                package_context['schema'] = schema

                existing = self._find_existing_package(pkg_dict)
                log.debug(
                    "Existing package found, updating %s..." % existing['id']
                )
                pkg_dict['name'] = existing['name']
                pkg_dict['id'] = existing['id']
                updated_pkg = get_action('package_update')(
                    package_context, pkg_dict)
                harvest_object.current = True
                harvest_object.package_id = updated_pkg['id']
                harvest_object.save()
                log.debug("Updated PKG: %s" % updated_pkg)
            except NotFound:
                # Change default schema to ignore lists of dicts, which
                # are stored in the '__junk' field
                schema = default_create_package_schema()
                schema['__junk'] = [ignore]

                package_context['schema'] = schema

                log.debug("No package found, create a new one!")

                # generate an id to reference it in the harvest_object
                pkg_dict['id'] = unicode(uuid.uuid4())

                log.info('Package with GUID %s does not exist, '
                         'let\'s create it' % harvest_object.guid)

                harvest_object.current = True
                harvest_object.package_id = pkg_dict['id']
                harvest_object.add()

                model.Session.execute(
                    'SET CONSTRAINTS harvest_object_package_id_fkey DEFERRED')
                model.Session.flush()

                created_pkg = get_action('package_create')(
                    package_context, pkg_dict)

                log.debug("Created PKG: %s" % created_pkg)

            Session.commit()
            return True

        except Exception as e:
            self._save_object_error(
                (
                    'Exception in import stage: %r / %s'
                    % (e, traceback.format_exc())
                ),
                harvest_object
            )
            return False

    def _create_new_context(self):
        # get the site user
        site_user = tk.get_action('get_site_user')(
            {'model': model, 'ignore_auth': True}, {})
        context = {
            'model': model,
            'session': Session,
            'user': site_user['name'],
        }
        return context

    def _get_existing_package_names(self, harvest_job):
        context = self._create_new_context()
        n = 500
        page = 1
        existing_package_names = []
        while True:
            search_params = {
                'fq': 'harvest_source_id:"{0}"'.format(harvest_job.source_id),
                'rows': n,
                'start': n * (page - 1),
            }
            try:
                existing_packages = get_action('package_search')(
                    context, search_params
                )
                if len(existing_packages['results']):
                    existing_package_names.extend(
                        [pkg['name'] for pkg in existing_packages['results']]
                    )
                    page = page + 1
                else:
                    break
            except NotFound:
                if page == 1:
                    log.debug('Could not find pkges for source %s'
                              % harvest_job.source_id)
        log.info('Found %d packages for source %s' %
                 (len(existing_package_names), harvest_job.source_id))
        return existing_package_names

    def _get_package_names_from_identifiers(self, package_identifiers):
        package_names = []
        for identifier in package_identifiers:
            pkg = {'identifier': identifier}
            try:
                existing_package = self._find_existing_package(pkg)
                package_names.append(existing_package['name'])
            except NotFound:
                continue

        return package_names

    def _check_for_deleted_datasets(self, harvest_job,
                                    gathered_dataset_identifiers):
        existing_package_names = self._get_existing_package_names(
            harvest_job
        )
        gathered_existing_package_names = self._get_package_names_from_identifiers(  # noqa
            gathered_dataset_identifiers
        )
        delete_names = list(set(existing_package_names) -
                            set(gathered_existing_package_names))
        # gather delete harvest ids
        delete_ids = []

        for package_name in delete_names:
            log.debug(
                'Dataset `%s` has been deleted at the source' %
                package_name)

            if self.config['delete_missing_datasets']:
                log.info('Add `%s` for deletion', package_name)

                obj = HarvestObject(
                    guid=package_name,
                    job=harvest_job,
                    extras=[HarvestObjectExtra(key='import_action',
                                               value='delete')]
                )
                obj.save()
                log.debug('adding ' + obj.guid + ' to the queue')

                delete_ids.append(obj.id)
        return delete_ids

    def _delete_dataset(self, package_dict):
        log.debug('deleting dataset %s' % package_dict['id'])
        context = self._create_new_context()
        get_action('dataset_purge')(
            context.copy(),
            package_dict
        )
        return True

    def _get_object_extra(self, harvest_object, key):
        for extra in harvest_object.extras:
            if extra.key == key:
                return extra.value
        return None

    def _get_geocat_permalink_relation(self, geocat_pkg_id):
        """gets backlink for geocat from configuration:
        the backlink consists of three parts:
        - a base url
        - a bookmark
        - the package id as it comes from geocat
        """
        if not self.config['permalink_valid']:
            return None

        permalink_bookmark_for_pkg = \
            self.config['permalink_bookmark'] + geocat_pkg_id
        permalink_url_for_pkg = urljoin(
            self.config['permalink_url'],
            permalink_bookmark_for_pkg)
        return {'url': permalink_url_for_pkg,
                'label': self.config['permalink_title']}


class GeocatConfigError(Exception):
    pass


def _derive_flat_title(title_dict):
    """localizes language dict if no language is specified"""
    return title_dict.get('de') or title_dict.get('fr') or title_dict.get('en') or title_dict.get('it') or ""  # noqa
