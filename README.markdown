[![Build Status](https://travis-ci.org/ckan/ckanext-deadoralive.png)](https://travis-ci.org/ckan/ckanext-deadoralive) [![Coverage Status](https://img.shields.io/coveralls/ckan/ckanext-deadoralive.svg)](https://coveralls.io/r/ckan/ckanext-deadoralive?branch=master)

ckanext-deadoralive
===================

A dead links checker plugin for CKAN: checks your CKAN site's resource URLs
for dead links.


Requirements
------------

Tested with CKAN 2.2 and Python 2.7. Python 2.6 is not supported!


Installation and Usage
----------------------

1. For now, you can install the plugin directly from GitHub.
   Activate your CKAN virtualenv and then:

        git clone https://github.com/ckan/ckanext-deadoralive.git
        cd ckanext-deadoralive
        python setup.py develop
        pip install -r requirements.txt

2. Add `deadoralive` to the `ckan.plugins` setting in your CKAN config file.

3. Create a user account for the link checker to use.

   Before you can run the link checker service you need a CKAN user account
   for it to use. I recommend creating a new user account
   just for the link checker rather than using an admin account, so the link
   checker can run with as few privileges as possible.

   You can create a user account by registering a new account using CKAN's web
   interface, or by using [CKAN's command-line interface](http://docs.ckan.org/en/latest/maintaining/paster.html#user-create-and-manage-users).

   Once you've created the user account for the link checker, add this config
   setting to the `[app:main]` section of your CKAN config file:

        # The names of the users who're allowed to access the deadoralive
        # plugin's API to post link checker results.
        # The API key of one of these users must be passed to deadoralive.py
        # when you run it.
        ckanext.deadoralive.authorized_users = deadoralive

   (In this example `deadoralive` is the name of the CKAN user account we
   created, but you can call this account whatever you like.)

4. Now restart CKAN by restarting your web server. You should see the links to
   the broken link report pages appear on your site. At first they will report
   no broken links - because you haven't checked the site for broken links yet.

5. Run the link checker service. With your CKAN virtualenv activated do:

        python deadoralive.py --url 'http://your.ckan.site.com' --apikey <your_api_key>

   The `--apikey` option must be the API key of the
   `ckanext.deadoralive.authorized_users` setting that you added to your config
   file (see above).

   To setup the link checker to run automatically you can add a cron job for
   it. On most UNIX systems you can add a cron job by running ``crontab -e`` to
   edit your crontab file. Assuming you have CKAN and ckanext-deadoralive
   installed in the default locations, add a line like the following to the
   file and save it::

        @hourly /usr/lib/ckan/default/bin/python /usr/lib/ckan/default/src/ckanext-deadoralive/deadoralive.py --url 'http://your.ckan.site.com' --apikey <your_api_key>

    As before, replace ``http://your.ckan.site.com`` with the URL of the CKAN
    site you want to check and ``<your_api_key>`` with the API key of the CKAN
    user that you want the link checker to run as.

    You can also use ``@daily`` or ``@weekly`` instead of ``@hourly`` if you
    want link checking to happen less often.


Running the Link Checker on a Different Machine
-----------------------------------------------

Although the ckanext-deadoralive extension has to be installed and activated on
the CKAN site that you want to check the links of, the link checker script
itself does not need to be run from the same machine. Because it does all
communication with the CKAN site via CKAN's API, you can run it from a
different server or from your laptop: just clone the repo and run
`deadoralive.py` as described above.


Optional Config Settings
------------------------

In the `[app:main]` section of the CKAN config file:

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


Creating Test Datasets
----------------------

To create some test datasets with working and broken links, do:

    python create_test_resources.py --url 'http://your.ckan.site.com' --apikey <your_api_key>

By default the `deadoralive` plugin won't mark a resource as broken unless it
has been broken for at least three consecutive link checks over a period of at
least three days. Also, after checking a link the plugin won't recheck it for
at least 24 hours.

For development, you probably want to relax these settings so you can mark your
test resources as broken quicker. Add these settings to your config file:

    ckanext.deadoralive.recheck_resources_after = 0
    ckanext.deadoralive.broken_resource_min_hours = 0

This will let you run the link checker many times in a row and recheck all of
the links, without waiting 24 hours to recheck a link. It'll also mark links as
broken as soon as they've been checked and found broken three times in a row,
regardless of the period of time the checks happened over.


Theory of Operation
-------------------

TODO.


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
