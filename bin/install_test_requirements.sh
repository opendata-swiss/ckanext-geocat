#!/bin/bash

WORKDIR=/__w/ckanext-geocat/ckanext-geocat

pip install --upgrade pip

# Install ckanext-geocat
echo "Install ckanext-geocat"
pip install -e "$WORKDIR"/[dev]

# Install ckanext dependencies
pip install -e git+https://github.com/ckan/ckanext-fluent.git#egg=ckanext-fluent
pip install -e git+https://github.com/ckan/ckanext-hierarchy.git#egg=ckanext-hierarchy
pip install -e git+https://github.com/ckan/ckanext-xloader.git#egg=ckanext-xloader
pip install -r https://raw.githubusercontent.com/ckan/ckanext-xloader/master/requirements.txt
pip install -e git+https://github.com/ckan/ckanext-harvest.git#egg=ckanext-harvest
pip install -r https://raw.githubusercontent.com/ckan/ckanext-harvest/master/requirements.txt
pip install -e git+https://github.com/ckan/ckanext-dcat.git#egg=ckanext-dcat
pip install -r https://raw.githubusercontent.com/ckan/ckanext-dcat/master/requirements-py2.txt
pip install -e git+https://github.com/ckan/ckanext-showcase.git#egg=ckanext-showcase
pip install -e git+https://github.com/ckan/ckanext-scheming.git@master#egg=ckanext-scheming

# Our ckanexts
# TODO: require main branch of all of these once they are updated to Python 3 and CKAN 2.11
# TODO: remove installing requirements.txt once these are switched to pyproject.toml (also check dependencies above)
pip install -e git+https://github.com/opendata-swiss/ckanext-dcatapchharvest.git@feat/upgrade_to_py3#egg=ckanext-dcatapchharvest
pip install -r https://raw.githubusercontent.com/opendata-swiss/ckanext-dcatapchharvest/feat/upgrade_to_py3/requirements.txt
pip install -e git+https://github.com/opendata-swiss/ckanext-harvester_dashboard.git@feat/upgrade_to_py3#egg=ckanext-harvester_dashboard
pip install -r https://raw.githubusercontent.com/opendata-swiss/ckanext-harvester_dashboard/feat/upgrade_to_py3/requirements.txt
pip install -e git+https://github.com/opendata-swiss/ckanext-password-policy.git@feat/upgrade_to_py3#egg=ckanext-password-policy
pip install -r https://raw.githubusercontent.com/opendata-swiss/ckanext-password-policy/feat/upgrade_to_py3/requirements.txt
pip install -e git+https://github.com/opendata-swiss/ckanext-subscribe.git#egg=ckanext-subscribe
pip install -r https://raw.githubusercontent.com/opendata-swiss/ckanext-subscribe/master/requirements.txt
pip install -e git+https://github.com/opendata-swiss/ckanext-switzerland-ng.git@upgrade_to_python3_ckan2_11#egg=ckanext-switzerland
pip install -r https://raw.githubusercontent.com/opendata-swiss/ckanext-switzerland-ng/upgrade_to_python3_ckan2_11/requirements.txt

echo "Replace default path to CKAN core config file with the one on the container"
sed -i -e 's/use = config:.*/use = config:\/srv\/app\/src\/ckan\/test-core.ini/' "$WORKDIR"/test.ini

echo "Replace default database url with the one for the postgres service"
sed -i -e 's/sqlalchemy.url = .*/sqlalchemy.url = postgresql:\/\/ckan_default:pass@postgres\/ckan_test/' "$WORKDIR"/test.ini

echo "Init db"
ckan -c "$WORKDIR"/test.ini db init
