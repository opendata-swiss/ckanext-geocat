#!/bin/bash
set -e

echo "This is travis-build.bash..."

echo "Updating GPG keys..."
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
curl -L https://packagecloud.io/github/git-lfs/gpgkey | sudo apt-key add -
wget -qO - https://www.mongodb.org/static/pgp/server-3.2.asc | sudo apt-key add -

echo "Adding archive repository for postgres..."
sudo rm /etc/apt/sources.list.d/pgdg*
echo "deb https://apt-archive.postgresql.org/pub/repos/apt trusty-pgdg-archive main" | sudo tee -a /etc/apt/sources.list
echo "deb-src https://apt-archive.postgresql.org/pub/repos/apt trusty-pgdg-archive main" | sudo tee -a /etc/apt/sources.list

echo "Removing old repository for cassandra..."
sudo rm /etc/apt/sources.list.d/cassandra*

echo "Installing the packages that CKAN requires..."
sudo apt-get update -qq
sudo apt-get install postgresql-$PGVERSION solr-jetty libcommons-fileupload-java:amd64=1.2.2-1

echo "Installing CKAN and its Python dependencies..."
git clone https://github.com/ckan/ckan
cd ckan
git checkout release-v2.2
python setup.py develop
pip install -r requirements.txt --allow-all-external
pip install -r dev-requirements.txt --allow-all-external
cd -

echo "Creating the PostgreSQL user and database..."
sudo -u postgres psql -c "CREATE USER ckan_default WITH PASSWORD 'pass';"
sudo -u postgres psql -c 'CREATE DATABASE ckan_test WITH OWNER ckan_default;'

echo "Initialising the database..."
cd ckan
paster db init -c test-core.ini
cd -

echo "Installing ckanext-harvest and its requirements..."
git clone https://github.com/ckan/ckanext-harvest
cd ckanext-harvest
python setup.py develop
pip install -r pip-requirements.txt
paster harvester initdb -c ../ckan/test-core.ini
cd -

echo "Installing ckanext-ckanext-geocat and its requirements..."
python setup.py develop
pip install -r dev-requirements.txt

echo "Moving test.ini into a subdir..."
mkdir subdir
mv test.ini subdir

echo "travis-build.bash is done."
