'''Test helper functions and classes.'''
import datetime

import ckan.config.middleware
import pylons.config as config
import webtest

import ckanext.deadoralive.model.results as results
import ckanext.deadoralive.logic.action.update as update


def make_broken(resources):
    """Make the given resources be reported as having broken links.

    By default a resource needs to have >= 3 consecutive failed link checks over
    a period of >= 3 days to be considered broken.

    """
    for resource in resources:
        one_day_ago = datetime.datetime.now() - datetime.timedelta(days=1)
        four_days_ago = datetime.datetime.now() - datetime.timedelta(days=4)
        seven_days_ago = datetime.datetime.now() - datetime.timedelta(days=7)
        data_dict = dict(
            resource_id=resource["id"],
            alive=False,
        )
        update.upsert(context={}, data_dict=data_dict,
                      last_checked=one_day_ago)
        update.upsert(context={}, data_dict=data_dict,
                      last_checked=four_days_ago)
        update.upsert(context={}, data_dict=data_dict,
                      last_checked=seven_days_ago)


def make_working(resources):
    """Make the given resources have successful link checker results."""
    for resource in resources:
        data_dict = dict(
            resource_id=resource["id"],
            alive=True,
        )
        update.upsert(context={}, data_dict=data_dict)


def _get_test_app():
    '''Return a webtest.TestApp for CKAN, with legacy templates disabled.

    For functional tests that need to request CKAN pages or post to the API.
    Unit tests shouldn't need this.

    '''
    config['ckan.legacy_templates'] = False
    app = ckan.config.middleware.make_app(config['global_conf'], **config)
    app = webtest.TestApp(app)
    return app


def _load_plugin(plugin):
    '''Add the given plugin to the ckan.plugins config setting.

    This is for functional tests that need the plugin to be loaded.
    Unit tests shouldn't need this.

    If the given plugin is already in the ckan.plugins setting, it won't be
    added a second time.

    :param plugin: the plugin to add, e.g. ``datastore``
    :type plugin: string

    '''
    plugins = set(config['ckan.plugins'].strip().split())
    plugins.add(plugin.strip())
    config['ckan.plugins'] = ' '.join(plugins)


class FunctionalTestBaseClass():
    '''A base class for functional test classes to inherit from.

    This handles loading the deadoralive plugin and resetting the CKAN config
    after your test class has run. It creates a webtest.TestApp at self.app for
    your class to use to make HTTP requests to the CKAN web UI or API.

    If you're overriding methods that this class provides, like setup_class()
    and teardown_class(), make sure to use super() to call this class's methods
    at the top of yours!

    '''
    @classmethod
    def setup_class(cls):
        # Make a copy of the Pylons config, so we can restore it in teardown.
        cls.original_config = config.copy()
        _load_plugin('deadoralive')
        cls.app = _get_test_app()

    def setup(self):
        import ckan.model as model
        model.Session.close_all()
        model.repo.rebuild_db()
        results.create_database_table()

    @classmethod
    def teardown_class(cls):
        # Restore the Pylons config to its original values, in case any tests
        # changed any config settings.
        config.clear()
        config.update(cls.original_config)
