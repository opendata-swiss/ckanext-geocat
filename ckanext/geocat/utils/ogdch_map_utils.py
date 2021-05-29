from datetime import datetime
from ckan.lib.munge import munge_tag

DEFAULT_RIGHTS = 'NonCommercialNotAllowed-CommercialNotAllowed-ReferenceRequired'  # noqa


def map_geocat_to_ogdch_identifier(geocat_identifier, organization_slug):
    return '@'.join([geocat_identifier, organization_slug])


def map_to_ogdch_publishers(geocat_publisher):
    dataset_publishers = []
    for publisher in geocat_publisher:
        dataset_publishers.append({'label': publisher})
    return dataset_publishers


def map_to_ogdch_datetime(datetime_value):
    try:
        d = datetime.strptime(
            datetime_value[0:len('YYYY-MM-DD')],
            '%Y-%m-%d'
        )
        # we have to calculate this manually since the
        # time library of Python 2.7 does not support
        # years < 1900, see OGD-751 and the time docs
        # https://docs.python.org/2.7/library/time.html
        epoch = datetime(1970, 1, 1)
        return int((d - epoch).total_seconds())
    except (ValueError, KeyError, TypeError, IndexError):
        raise ValueError("Could not parse datetime")


def map_to_ogdch_keywords(geocat_keywords):
    ogdch_keywords = {'fr': [], 'de': [], 'en': [], 'it': []}
    for keyword in geocat_keywords:
        for lang, geocat_keyword in keyword.items():
            if geocat_keyword != 'opendata.swiss' and lang in ['fr', 'de', 'en', 'it']:  # noqa
                ogdch_keywords[lang].append(munge_tag(geocat_keyword))  # noqa
    return ogdch_keywords
