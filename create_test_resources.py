#!/usr/bin/env python2.7
"""A CKAN API client that creates test datasets and resources.

Creates test resources with working and broken links. Meant for testing
deadoralive.py in development.

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


def main(n=200):
    parser = argparse.ArgumentParser()
    parser.add_argument("--url")
    parser.add_argument("--apikey")
    parsed_args = parser.parse_args()
    ckan_url = parsed_args.url
    apikey = parsed_args.apikey

    ckan = ckanapi.RemoteCKAN(ckan_url, apikey=apikey)

    logger.info("Creating test organization.")
    try:
        ckan.action.organization_create(name="test_organization")
    except ckanapi.ValidationError as err:
        if err.error_dict == {
                u'__type': u'Validation Error',
                u'name': [u'Group name already exists in database']}:
            logger.info("Test organization already exists, skipping.")
        else:
            raise

    logger.info("Creating test dataset.")
    try:
        ckan.action.package_create(name="test_dataset",
                                   owner_org="test_organization")
    except ckanapi.ValidationError as err:
        if err.error_dict == {
                u'__type': u'Validation Error',
                u'name': [u'That URL is already in use.']}:
            logger.info("Test dataset already exists, skipping.")
        else:
            raise

    for i in range(0, n):
        if random.random() < 0.5:
            resource = ckan.action.resource_create(
                package_id="test_dataset",
                url="broken_link",
            )
            logger.info("Created test resource {0} with broken link.".format(
                resource["id"]))
        else:
            # Create a CKAN resource and upload a file to it.
            # Note that we still have to pass ``url`` to package create even
            # though it isn't used - otherwise CKAN has a validation error.
            resource = ckan.action.resource_create(
                package_id="test_dataset",
                url="foobar",
                upload=open("test_data_file.txt"),
            )
            logger.info("Created test resource {0} by uploading file.".format(
                resource["id"]))


if __name__ == "__main__":
    main()
