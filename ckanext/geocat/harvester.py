# -*- coding: utf-8 -*-

import traceback
import uuid

from ckan.lib.helpers import json
from ckanext.harvest.model import HarvestObject
from ckanext.harvest.harvesters import HarvesterBase
import ckanext.geocat.metadata as md
import ckanext.geocat.xml_loader as loader
from ckan.logic import get_action, NotFound
from ckan import model
from ckan.model import Session

import logging
log = logging.getLogger(__name__)


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

    def _set_config(self, config_str):
        if config_str:
            self.config = json.loads(config_str)
        else:
            self.config = {}

        if 'user' not in self.config:
            self.config['user'] = self.HARVEST_USER

        log.debug('Using config: %r' % self.config)

    def _find_existing_package(self, package_dict):
        data_dict = {'identifier': package_dict['identifier']}
        package_show_context = {'model': model, 'session': Session,
                                'ignore_auth': True}
        return get_action('ogdch_dataset_by_identifier')(
            package_show_context, data_dict)

    def gather_stage(self, harvest_job):
        log.debug('In GeocatHarvester gather_stage')

        try:
            self._set_config(harvest_job.source.config)
        except GeocatConfigError, e:
            self._save_gather_error(
                'Config value missing: %s' % str(e),
                harvest_job
            )
            return []

        csw_url = None
        try:
            harvest_obj_ids = []
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

            log.debug('IDs: %r' % harvest_obj_ids)

            return harvest_obj_ids
        except Exception, e:
            self._save_gather_error(
                'Unable to get content for URL: %s: %s / %s'
                % (csw_url, str(e), traceback.format_exc()),
                harvest_job
            )
            return []

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
        except Exception, e:
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
                    existing_see_alsos.append(identifier)
                except NotFound:
                    continue
            pkg_dict['see_alsos'] = existing_see_alsos

            pkg_dict['owner_org'] = self.config['organization']
            pkg_dict['resources'] = dist_list
            pkg_dict['name'] = self._gen_new_name(pkg_dict['title']['de'])

            # legal basis
            legal_basis_url = self.config.get('legal_basis_url', None)
            if legal_basis_url:
                pkg_dict['relations'].append({
                    'url': legal_basis_url,
                    'label': 'legal_basis'
                })

            log.debug('package dict: %s' % pkg_dict)

            package_context = {'ignore_auth': True}
            try:
                existing = self._find_existing_package(pkg_dict)
                log.debug(
                    "Existing package found, updating %s..." % existing['id']
                )
                pkg_dict['name'] = existing['name']
                pkg_dict['id'] = existing['id']
                updated_pkg = get_action('package_update')(package_context pkg_dic)citly provide a package ID
                harvest_object.current = True
                harvest_object.package_id = updated_pkg['id']
                harvest_object.save()
                log.debug("Updated PKG: %s" % updated_pkg)
            except NotFound:
                log.debug("No package found, create a new one!")

                # We need to explicitly provide a package ID
                pkg_dict['id'] = unicode(uuid.uuid4())

                # save the reference on the harvest object
                harvest_object.package_id = pkg_dict['id']
                harvest_object.current = True
                harvest_object.add()

                # Defer constraints and flush so the dataset can be indexed with
                # the harvest object id (on the after_show hook from the harvester
                # plugin)
                model.Session.execute('SET CONSTRAINTS harvest_object_package_id_fkey DEFERRED')
                model.Session.flush()

                created_pkg = get_action('package_create')(package_context, pkg_dict)
                log.debug("Created PKG: %s" % created_pkg)

            Session.commit()
            return True

        except Exception, e:
            self._save_object_error(
                (
                    'Exception in import stage: %r / %s'
                    % (e, traceback.format_exc())
                ),
                harvest_object
            )
            return False


class GeocatConfigError(Exception):
    pass
