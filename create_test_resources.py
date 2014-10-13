# -*- coding: utf-8 -*-
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


def random_author():
    return random.choice((
        dict(name=u"äüthör one", email=u"äüthör_1@authors.com"),
        dict(name=u"äüthör two", email=u"author_2@authors.com"),
        dict(name=u"äüthör three", email=u"äüthör_3@authors.com"),
        dict(name=None, email=None),
        dict(name=u"äüthör three", email=None),
        dict(name=None, email=u"äüthör_3@authors.com"),
    ))


def random_maintainer():
    return random.choice((
        dict(name=u"mäintainër one", email=u"mäintainër_1@authors.com"),
        dict(name=u"mäintainër two", email=u"mäintainër_2@authors.com"),
        dict(name=u"mäintainër three", email=u"mäintainër_3@authors.com"),
        dict(name=None, email=None),
        dict(name=u"mäintainër three", email=None),
        dict(name=None, email=u"mäintainër_3@authors.com"),
    ))


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
        org_name = "test_organisation_{0}".format(org_num)
        org_title = u"Test Örgänißation {0}".format(org_num)
        logger.info("Creating test organization {0}.".format(org_name))
        try:
            ckan.action.organization_create(name=org_name, title=org_title)
        except ckanapi.ValidationError as err:
            if err.error_dict == {
                    u'__type': u'Validation Error',
                    u'name': [u'Group name already exists in database']}:
                logger.info("Organization already exists, skipping.")
            else:
                raise

        for dataset_num in range(0, random_number_of_datasets()):
            dataset_name = "org_{0}_dataset_{1}".format(org_num, dataset_num)
            dataset_title = u"Org {0} dätaßët {1}".format(org_num, dataset_num)
            logger.info("Creating test dataset {0}.".format(dataset_name))
            try:
                author = random_author()
                maintainer = random_maintainer()
                ckan.action.package_create(
                    name=dataset_name, title=dataset_title, owner_org=org_name,
                    author=author["name"],
                    author_email=author["email"],
                    maintainer=maintainer["name"],
                    maintainer_email=maintainer["email"])
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
                        name=u"tëßt resource",
                        package_id=dataset_name,
                        url=u"bröken_link",
                    )
                    logger.info("Created test resource {0} with broken link.".format(resource["id"]))
                else:
                    # Create a CKAN resource and upload a file to it.  Note that
                    # we still have to pass ``url`` to package create even
                    # though it isn't used - otherwise CKAN has a validation
                    # error.
                    resource = ckan.action.resource_create(
                        name="tëßt resource",  # Deliberately don't use a u".."
                                               # string literal here because it
                                               # makes requests crash!
                        package_id=dataset_name,
                        url=None,
                        upload=open("test_data_file.txt"),
                    )
                    logger.info("Created test resource {0} by uploading file.".format(resource["id"]))


if __name__ == "__main__":
    main()
