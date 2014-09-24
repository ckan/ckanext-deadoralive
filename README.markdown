[![Build Status](https://travis-ci.org/seanh/ckanext-deadoralive.png)](https://travis-ci.org/seanh/ckanext-deadoralive) [![Coverage Status](https://img.shields.io/coveralls/seanh/ckanext-deadoralive.svg)](https://coveralls.io/r/seanh/ckanext-deadoralive?branch=master)

ckanext-deadoralive
===================

A dead links checker plugin for CKAN: checks your CKAN site's resource URLs
for dead links.

Requirements
------------

Tested with CKAN 2.2 and Python 2.7. Python 2.6 is not supported!


Installation
------------


Config Settings
---------------

In the `[app:main]` section of the CKAN config file:


    # The names of the users who're allowed to access the deadoralive plugin's
    # API to post link checker results.
    # The API key of one of these users must be passed to deadoralive.py when
    # you run it.
    # We recommend creating a special deadoralive user for this purpose that is
    # not a sysadmin or organization admin user - that way the link checker
    # can run with the minimum permissions that it needs.
    ckanext.deadoralive.authorized_users = deadoralive

    # The minimum number of hours to wait before re-checking a resource
    # (optional, default: 24).
    ckanext.deadoralive.recheck_resources_after = 24

    # The minimum number of hours to wait for a check result for a resource
    # to come back before timing out and giving the resource out again to
    # another link checker task (optional, default: 2).
    ckanext.deadoralive.recheck_resources_after = 2

    # The minimum number of times that checking a resource's link must fail
    # consecutively before we mark that resource as broken in CKAN.
    ckanext.deadoralive.broken_resource_min_fails = 3

    # The minimum number of hours that a resource's link must be broken for
    # before we mark that resource as broken in CKAN.
    ckanext.deadoralive.broken_resource_min_hours = 36



Theory of Operation
-------------------

It's a CKAN extension plus a link checker cron job.


Running the Tests
-----------------

Note that you should have the `release-v2.2` branch of CKAN checked out when
you run these tests. The `ckanext-deadoralive` `master` branch is currently
tested against CKAN's `release-v2.2` branch on Travis.

From the `ckanext-deadoralive` directory run:

    nosetests --nologcapture --with-pylons=test.ini

To run the tests and produce a coverage report, first make sure you have
coverage installed in your virtualenv (`pip install coverage`) then run:

    nosetests --nologcapture --with-pylons=test.ini --with-coverage --cover-package=ckanext.deadoralive --cover-inclusive --cover-erase --cover-tests
