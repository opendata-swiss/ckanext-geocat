# -*- coding: utf-8 -*-

import traceback

from ckan.lib.helpers import json
from ckanext.harvest.model import HarvestObject, HarvestObjectExtra
from ckanext.harvest.harvesters import HarvesterBase
from ckanext.geocat.utils import search_utils, csw_processor, ogdch_map_utils, csw_mapping  # noqa
from ckanext.geocat.utils.vocabulary_utils import \
  (VALID_TERMS_OF_USE, DEFAULT_TERMS_OF_USE)
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
HARVEST_USER = 'harvest'


class GeocatHarvester(HarvesterBase):
    '''
    The harvester for geocat
    '''
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
        except Exception as e:
            raise ValueError(
                    'Configuration could not be parsed. An error {} occured'
                    .format(e)
                )

        if 'delete_missing_datasets' in config_obj:
            if not isinstance(config_obj['delete_missing_datasets'], bool):
                raise ValueError('delete_missing_dataset must be boolean')

        if 'rights' in config_obj:
            if not config_obj['rights'] in VALID_TERMS_OF_USE:
                raise ValueError('{} is not valid as terms of use'
                                 .format(config_obj['rights']))
        return config

    def _set_config(self, config_str, harvest_source_id):
        if config_str:
            self.config = json.loads(config_str)
        else:
            self.config = {}

        self.config['rights'] = self.config.get('rights', DEFAULT_TERMS_OF_USE)
        if not self.config['rights'] in VALID_TERMS_OF_USE:
            self.config['rights'] = DEFAULT_TERMS_OF_USE
        self.config['delete_missing_datasets'] = \
            self.config.get('delete_missing_datasets', False)

        self.config['geocat_perma_link_label'] = \
            tk.config.get('ckanext.geocat.permalink_title',
                          DEFAULT_PERMA_LINK_LABEL)
        self.config['geocat_perma_link_url'] = \
            self.config.get('geocat_perma_link_url',
                            tk.config.get('geocat_perma_link_url',
                                          DEFAULT_PERMA_LINK_URL))

        self.config['legal_basis_url'] = \
            self.config.get('legal_basis_url', None)

        organization_slug = \
            search_utils.get_organization_slug_for_harvest_source(
                harvest_source_id)
        self.config['organization'] = organization_slug

        log.debug('Using config: %r' % self.config)

    def gather_stage(self, harvest_job):
        log.debug('In GeocatHarvester gather_stage')
        self._set_config(harvest_job.source.config, harvest_job.source.id)

        csw_url = harvest_job.source.url

        try:
            csw_data = csw_processor.GeocatCatalogueServiceWeb(url=csw_url)
            gathered_geocat_identifiers = csw_data.get_geocat_id_from_csw()
        except Exception as e:
            self._save_gather_error(
                'Unable to get content for URL: %s: %s / %s'
                % (csw_url, str(e), traceback.format_exc()),
                harvest_job
            )
            return []

        existing_dataset_infos = \
            search_utils.get_dataset_infos_for_organization(
                organization_name=self.config['organization'],
                harvest_source_id=harvest_job.source_id,
            )

        gathered_ogdch_identifiers = \
            [ogdch_map_utils.map_geocat_to_ogdch_identifier(
                geocat_identifier=geocat_identifier,
                organization_slug=self.config['organization'])
             for geocat_identifier in gathered_geocat_identifiers]

        all_ogdch_identifiers = \
            set(gathered_ogdch_identifiers + existing_dataset_infos.keys())

        packages_to_delete = search_utils.get_packages_to_delete(
            existing_dataset_infos=existing_dataset_infos,
            gathered_ogdch_identifiers=gathered_ogdch_identifiers,
        )

        csw_map = csw_mapping.GeoMetadataMapping(
            organization_slug=self.config['organization'],
            geocat_perma_link=self.config['geocat_perma_link_url'],
            geocat_perma_label=self.config['geocat_perma_link_label'],
            legal_basis_url=self.config['legal_basis_url'],
            default_rights=self.config['rights'],
            valid_identifiers=all_ogdch_identifiers,
        )

        harvest_obj_ids = self.map_geocat_dataset(
            csw_data,
            csw_map,
            gathered_geocat_identifiers,
            gathered_ogdch_identifiers,
            harvest_job)

        log.debug('IDs: %r' % harvest_obj_ids)

        if self.config['delete_missing_datasets']:
            delete_harvest_object_ids = \
                self.delete_geocat_ids(
                    harvest_job,
                    harvest_obj_ids,
                    packages_to_delete
                )
            harvest_obj_ids.extend(delete_harvest_object_ids)

        return harvest_obj_ids

    def delete_geocat_ids(self,
                          harvest_job,
                          harvest_obj_ids,
                          packages_to_delete):
        delete_harvest_obj_ids = []
        for package_info in packages_to_delete:
            obj = HarvestObject(
                guid=package_info[1].name,
                job=harvest_job,
                extras=[HarvestObjectExtra(key='import_action',
                                           value='delete')])
            obj.save()
            delete_harvest_obj_ids.append(obj.id)
        return delete_harvest_obj_ids

    def map_geocat_dataset(self,
                           csw_data,
                           csw_map,
                           gathered_geocat_identifiers,
                           gathered_ogdch_identifiers,
                           harvest_job):
        mapped_harvest_obj_ids = []
        for geocat_id in gathered_geocat_identifiers:

            ogdch_identifier = ogdch_map_utils.map_geocat_to_ogdch_identifier(
                geocat_identifier=geocat_id,
                organization_slug=self.config['organization'])
            if ogdch_identifier in gathered_ogdch_identifiers:
                try:
                    csw_record_as_string = csw_data.get_record_by_id(geocat_id)
                except Exception as e:
                    self._save_gather_error(
                        'Error when reading csw record form source: %s %r / %s'
                        % (ogdch_identifier, e, traceback.format_exc()),
                        harvest_job)
                    continue

                try:
                    dataset_dict = csw_map.get_metadata(csw_record_as_string,
                                                        geocat_id)
                except Exception as e:
                    self._save_gather_error(
                        'Error when mapping csw data to dcat: %s %r / %s'
                        % (ogdch_identifier, e, traceback.format_exc()),
                        harvest_job)
                    continue

                try:
                    harvest_obj = \
                        HarvestObject(guid=ogdch_identifier,
                                      job=harvest_job,
                                      content=json.dumps(dataset_dict))
                    harvest_obj.save()
                except Exception as e:
                    self._save_gather_error(
                        'Error when processsing dataset: %s %r / %s'
                        % (ogdch_identifier, e, traceback.format_exc()),
                        harvest_job)
                    continue
                else:
                    mapped_harvest_obj_ids.append(harvest_obj.id)
        return mapped_harvest_obj_ids

    def fetch_stage(self, harvest_object):
        return True

    def import_stage(self, harvest_object):  # noqa

        log.debug('In GeocatHarvester import_stage')

        if not harvest_object:
            log.error('No harvest object received')
            self._save_object_error(
                'No harvest object received',
                harvest_object
            )
            return False

        import_action = \
            search_utils.get_value_from_object_extra(harvest_object.extras,
                                                     'import_action')
        if import_action and import_action == 'delete':
            log.debug('import action: %s' % import_action)
            harvest_object.current = False
            return self._delete_dataset({'id': harvest_object.guid})

        if harvest_object.content is None:
            self._save_object_error('Empty content for object %s' %
                                    harvest_object.id,
                                    harvest_object, 'Import')
            return False

        try:
            pkg_dict = json.loads(harvest_object.content)
        except ValueError:
            self._save_object_error('Could not parse content for object {0}'
                                    .format(harvest_object.id), harvest_object, 'Import')  # noqa
            return False

        pkg_info = \
            search_utils.find_package_for_identifier(harvest_object.guid)
        context = {
            'ignore_auth': True,
            'user': HARVEST_USER,
        }
        try:
            if pkg_info:
                # Change default schema to ignore lists of dicts, which
                # are stored in the '__junk' field
                schema = default_update_package_schema()
                context['schema'] = schema
                schema['__junk'] = [ignore]
                pkg_dict['name'] = pkg_info.name
                pkg_dict['id'] = pkg_info.package_id
                search_utils.map_resources_to_ids(pkg_dict, pkg_info)
                updated_pkg = \
                    tk.get_action('package_update')(context, pkg_dict)
                harvest_object.current = True
                harvest_object.package_id = updated_pkg['id']
                harvest_object.save()
                log.debug("Updated PKG: %s" % updated_pkg)
            else:
                flat_title = _derive_flat_title(pkg_dict['title'])
                if not flat_title:
                    self._save_object_error(
                        'Unable to derive name from title %s'
                        % pkg_dict['title'], harvest_object, 'Import')
                    return False
                pkg_dict['name'] = self._gen_new_name(flat_title)
                schema = default_create_package_schema()
                context['schema'] = schema
                schema['__junk'] = [ignore]
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

                created_pkg = \
                    tk.get_action('package_create')(context, pkg_dict)

                log.debug("Created PKG: %s" % created_pkg)

            Session.commit()
            return True

        except Exception as e:
            self._save_object_error(
                ('Exception in import stage: %r / %s'
                 % (e, traceback.format_exc())), harvest_object)
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

    def _delete_dataset(self, package_dict):
        log.debug('deleting dataset %s' % package_dict['id'])
        context = self._create_new_context()
        tk.get_action('dataset_purge')(
            context.copy(),
            package_dict
        )
        return True

    def _get_geocat_permalink_relation(self, geocat_pkg_id):
        return {'url': self.config['geocat_perma_link_url'] + geocat_pkg_id,
                'label': self.config['geocat_perma_link_label']}


class GeocatConfigError(Exception):
    pass


def _derive_flat_title(title_dict):
    """localizes language dict if no language is specified"""
    return title_dict.get('de') or title_dict.get('fr') or title_dict.get('en') or title_dict.get('it') or ""  # noqa
