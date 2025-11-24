[![Build Status](https://app.travis-ci.com/opendata-swiss/ckanext-geocat.svg?branch=master)](https://app.travis-ci.com/opendata-swiss/ckanext-geocat)

ckanext-geocat
=============

This extension harvests data from the Swiss CSW service [geocat.ch](http://geocat.ch) to the Swiss open data portal
[opendata.swiss](https://opendata.swiss). The source format is ISO-19139_che (Swiss version of ISO-19139) and the target
format is DCAT-AP Switzerland.


## Requirements

CKAN >= 2.11

## Installation

To install ckanext-geocat:

1. Activate your CKAN virtual environment, for example:

     . /usr/lib/ckan/default/bin/activate

2. Install the ckanext-geocat Python package into your virtual environment:

     pip install ckanext-geocat

3. Add ``geocat`` to the ``ckan.plugins`` setting in your CKAN
   config file (by default the config file is located at
   ``/etc/ckan/default/production.ini``).

4. Restart CKAN. For example if you've deployed CKAN with Apache on Ubuntu:

     sudo service apache2 reload


## Config Settings

For ckanext-geocat config settings, see `ckanext/geocat/config_declaration.yaml`.

Config options that can be set per harvest source, in the `config` field, as JSON:

* `cql_query`: The CQL query to be used when requesting the CSW service (default: `subject`)
* `cql_search_term`: The search term to be used with the CQL query (default: `opendata.swiss`)
* `rights`: The fall back terms of use to be associated with the harvested datasets if terms of use is not specified for
  them (default: `NonCommercialNotAllowed-CommercialNotAllowed-ReferenceRequired`)
* `delete_missing_datasets`: Boolean flag (true/false) to determine if this harvester should delete existing datasets
  that are no longer included in the harvest-source (default: `false`)
* `geocat_perma_link_url`: The URL to Geocat, used to construct geocat permalinks. The default is
  `https://www.geocat.ch/geonetwork/srv/ger/catalog.search#/metadata/`. The permalink for a dataset is formed by
  appending its Geocat identifier. For a test harvester, the permalink might need to point to the test Geocat instance.
  The geocat permalink is used as the value for `dct:relation` for a dataset.
* `legal_basis_url`: the link to the legal documents that relate to the publication of the dataset. This is also added
   to `dct:relation` for all harvested datasets in case it is provided
* [**Deprecated**] `cql`: The CQL query to be used when requesting the CSW service (default: `subject = 'opendata.swiss'`)


## CLI Commands

This extension provides a number of CLI commands to query/debug the results of the CSW server.

They give you the power to check on a remote csw source with search paramterers or a specific record id.
You can either get all remote record ids for a search, or map one remote record to a DCAT dataset.

### `list`

To list all IDs from the defined CSW server use the `list` command:

- it expects the url of the remote csw source
- you can also add a query key and a query term
- it brings back all records from the remote source; in case query key and term are set
  it brings back all records where the query key has the given value
   
Examples:   

```
ckan geocat list https://www.geocat.ch/geonetwork/srv/eng/csw-ZH/
ckan geocat list https://www.geocat.ch/geonetwork/srv/eng/csw-ZH/ --query keyword --term opendata.swiss
```

### `dataset`

To get a specific record (by ID), use the `dataset` command.
You can get the ID by first using the `list` command above:

```
ckan geocat dataset https://www.geocat.ch/geonetwork/srv/eng/csw-ZH/ "1eac72b1-068d-4272-b011-d0010cc4bf676"
```

The output shows the dataset as it would be mapped by the harvester.

### `help`

Use the command with `help` to check get help for the other two commands.

```
ckan geocat help
```

## Analyzing geocat original data

In order to take a look at the geocat original data:

- Follow the permalink of the dataset to geocat
- Get the link to the xml version of the data: this should be similar to `https://www.geocat.ch/geonetwork/srv/ger/xml.metadata.get?uuid=170800fb-e85c-42b7-8c4b-ba33b364b79f`
- Go to https://codebeautify.org/Xpath-Tester
- Load the data in from URL
- Explore with XPath

## CSW data: check harvest source per API

Sometimes it is useful to directly check the harvest source per API.
More documentation is available here:
https://geonetwork-opensource.org/manuals/2.10.4/eng/developer/xml_services/csw_services.html.

```
<harvest-source-url>?service=CSW&version=2.0.2&request=GetRecords
<harvest-source-url>?service=CSW&version=2.0.2&request=GetRecordById&id=<geocat-id>&elementsetname=full&outputSchema=http://www.isotc211.org/2005/gmd
``` 

## Development Installation

To install ckanext-geocat for development, activate your CKAN virtualenv and
do::

    git clone https://github.com/opendata-swiss/ckanext-geocat.git
    cd ckanext-geocat
    pip install -e .[dev]
