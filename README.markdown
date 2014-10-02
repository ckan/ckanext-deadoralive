[![Build Status](https://travis-ci.org/ckan/ckanext-deadoralive.png)](https://travis-ci.org/ckan/ckanext-deadoralive) [![Coverage Status](https://img.shields.io/coveralls/ckan/ckanext-deadoralive.svg)](https://coveralls.io/r/ckan/ckanext-deadoralive?branch=master)

ckanext-deadoralive
===================

ckanext-deadoralive is a CKAN extension for the [Dead or Alive link checker service](https://github.com/ckan/deadoralive).
It provides the API that enables a CKAN site to be checked by the link checker,
handles saving the results posted by the link checker in CKAN's database and
adds various broken link reports to the CKAN site.

TODO: Screenshots of the reports.


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

5. Now go over to [Dead or Alive](https://github.com/ckan/deadoralive) and
   install the link checker (either on the same machine where CKAN is installed
   or on a different machine - it doesn't matter). The API key that you
   configure the link checker with should be the API key of the user you
   created in step 3 above. Run the link checker against your CKAN site and
   you'll start to see broken link reports appear on the site.


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


Development
-----------

To install the plugin for development, activate your CKAN virtualenv and do:

        git clone https://github.com/ckan/ckanext-deadoralive.git
        cd ckanext-deadoralive
        python setup.py develop
        pip install -r dev-requirements.txt


### Creating Test Datasets

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


### Running the Tests

Note that you should have the `release-v2.2` branch of CKAN checked out when
you run these tests. The `ckanext-deadoralive` `master` branch is currently
tested against CKAN's `release-v2.2` branch on Travis.

From the `ckanext-deadoralive` directory run:

    nosetests --nologcapture --with-pylons=test.ini

To run the tests and produce a coverage report, first make sure you have
coverage installed in your virtualenv (`pip install coverage`) then run:

    nosetests --nologcapture --with-pylons=test.ini --with-coverage --cover-package=ckanext.deadoralive --cover-inclusive --cover-erase --cover-tests
