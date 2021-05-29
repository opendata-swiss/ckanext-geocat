DEFAULT_RIGHTS = 'NonCommercialNotAllowed-CommercialNotAllowed-ReferenceRequired'  # noqa


def map_geocat_to_ogdch_identifier(geocat_identifier, organization_slug):
    return '@'.join([geocat_identifier, organization_slug])


def map_to_ogdch_publishers(geocat_publisher):
    dataset_publishers = []
    for publisher in geocat_publisher:
        dataset_publishers.append({'label': publisher})
    return dataset_publishers
