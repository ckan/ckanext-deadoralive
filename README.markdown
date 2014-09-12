[![Build Status](https://travis-ci.org/seanh/ckanext-deadoralive.png)](https://travis-ci.org/seanh/ckanext-deadoralive) [![Coverage Status](https://coveralls.io/repos/seanh/ckanext-deadoralive/badge.png?branch=master)](https://coveralls.io/r/seanh/ckanext-deadoralive?branch=master)

ckanext-deadoralive
===================

A dead links checker plugin for CKAN: checks your CKAN site's resource URLs
for dead links.


Theory of Operation
-------------------

It's a CKAN extension plus a link checker cron job.


Running the Tests
-----------------

From the `ckanext-deadoralive` directory run:

    nosetests --nologcapture --with-pylons=test.ini

To run the tests and produce a coverage report, first make sure you have
coverage installed in your virtualenv (`pip install coverage`) then run:

    nosetests --nologcapture --with-pylons=test.ini --with-coverage --cover-package=ckanext.deadoralive --cover-inclusive --cover-erase --cover-tests
