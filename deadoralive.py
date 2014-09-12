#!/usr/bin/env python2.7
"""A CKAN API client that checks a CKAN site's resource URLs for dead links.

It's designed to work with the deadoralive plugin from the ckanext-deadoralive
extension: it only works against CKAN sites that have this plugin activated.

"""
import argparse
import logging

import requests
import requests.exceptions

import ckanapi


# TODO: Add options for verbose and debug logging.
# TODO: Add option for logging to file.
logger = logging.getLogger("deadoralive")
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - "
                              "%(message)s")
ch.setFormatter(formatter)
logger.addHandler(ch)


def main(n=50):
    parser = argparse.ArgumentParser()
    parser.add_argument("--url")
    parser.add_argument("--apikey")
    parsed_args = parser.parse_args()
    ckan_url = parsed_args.url
    apikey = parsed_args.apikey

    ckan = ckanapi.RemoteCKAN(ckan_url, apikey=apikey)
    resource_ids_to_check = (
        ckan.action.ckanext_deadoralive_get_resources_to_check(n=n))
    for resource_id in resource_ids_to_check:
        try:
            resource_dict = ckan.action.resource_show(id=resource_id)
        except ckanapi.NotAuthorized:
            logger.info("This link checker was not authorized to access "
                        "resource {0}, skipping.".format(resource_id))
            continue
        url = resource_dict.get("url")
        alive = None
        try:
            response = requests.get(url)
            logger.info("Checking URL {0} of resource {1} succeeded with "
                        "status {2}:".format(url, resource_id,
                                             response.status_code))
            alive = True

        except requests.exceptions.RequestException as err:
            logger.info("Checking URL {0} of resource {1} "
                        "failed with error {2}:".format(url, resource_id, err))
            alive = False

        assert alive in (True, False)
        ckan.action.ckanext_deadoralive_save_link_checker_result(
            resource_id=resource_id, alive=alive)


if __name__ == "__main__":
    main()
