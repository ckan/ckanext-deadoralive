#!/usr/bin/env python2.7
"""A CKAN API client that creates test datasets and resources.

Creates test organizations, datasets and resources, some with working and some
with broken resource links. Meant for testing deadoralive.py in development.

Run `create_test_resources.py -h` for usage.

"""
import argparse
import logging
import random

import ckanapi


logger = logging.getLogger("create_test_resources")
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - "
                              "%(message)s")
ch.setFormatter(formatter)
logger.addHandler(ch)


def random_author_email():
    return random.choice(("author_1@authors.com", "author_2@authors.com",
                          "author_3@authors.com", None))


def random_maintainer_email():
    return random.choice(("maintainer_1@authors.com",
                          "maintainer_2@authors.com",
                          "maintainer_3@authors.com", None))


def random_number_of_resources():
    return random.choice(range(0, 7))


def random_number_of_datasets():
    return random.choice(range(0, 11))


def random_number_of_organizations():
    return random.choice(range(0, 5))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True)
    parser.add_argument("--apikey")
    parsed_args = parser.parse_args()
    ckan_url = parsed_args.url
    apikey = parsed_args.apikey

    ckan = ckanapi.RemoteCKAN(ckan_url, apikey=apikey)

    for org_num in range(0, random_number_of_organizations()):
        org_name = "test_organization_{0}".format(org_num)
        logger.info("Creating test organization {0}.".format(org_name))
        try:
            ckan.action.organization_create(name=org_name)
        except ckanapi.ValidationError as err:
            if err.error_dict == {
                    u'__type': u'Validation Error',
                    u'name': [u'Group name already exists in database']}:
                logger.info("Organization already exists, skipping.")
            else:
                raise

        for dataset_num in range(0, random_number_of_datasets()):
            dataset_name = "org_{0}_dataset_{1}".format(org_num, dataset_num)
            logger.info("Creating test dataset {0}.".format(dataset_name))
            try:
                ckan.action.package_create(
                    name=dataset_name, owner_org=org_name,
                    author_email=random_author_email(),
                    maintainer_email=random_maintainer_email())
            except ckanapi.ValidationError as err:
                if err.error_dict == {
                        u'__type': u'Validation Error',
                        u'name': [u'That URL is already in use.']}:
                    logger.info("Dataset already exists, skipping.")
                else:
                    raise

            for i in range(0, random_number_of_resources()):
                if random.random() < 0.5:
                    resource = ckan.action.resource_create(
                        package_id=dataset_name,
                        url="broken_link",
                    )
                    logger.info("Created test resource {0} with broken link.".format(resource["id"]))
                else:
                    # Create a CKAN resource and upload a file to it.  Note that
                    # we still have to pass ``url`` to package create even
                    # though it isn't used - otherwise CKAN has a validation
                    # error.
                    resource = ckan.action.resource_create(
                        package_id=dataset_name,
                        url=None,
                        upload=open("test_data_file.txt"),
                    )
                    logger.info("Created test resource {0} by uploading file.".format(resource["id"]))


if __name__ == "__main__":
    main()
