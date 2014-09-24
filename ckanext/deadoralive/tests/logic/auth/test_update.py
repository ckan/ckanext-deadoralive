import nose.tools

import ckan.model as model
import ckan.new_tests.factories as factories
import ckan.plugins.toolkit as toolkit
import ckanext.deadoralive.config as config
import ckanext.deadoralive.tests.helpers as custom_helpers


class TestUpsert(custom_helpers.FunctionalTestBaseClass):

    def test_configured_users_can_upsert(self):
        user = factories.User()
        config.authorized_users = [user["name"]]
        context = dict(user=user["name"], model=model)
        assert custom_helpers.call_auth(
            "ckanext_deadoralive_upsert", context=context) is True

    def test_other_users_cannot_upsert(self):
        user_1 = factories.User()
        user_2 = factories.User()
        config.authorized_users = [user_1["name"]]
        context = dict(user=user_2["name"], model=model)
        nose.tools.assert_raises(toolkit.NotAuthorized,
                                 custom_helpers.call_auth,
                                 "ckanext_deadoralive_upsert", context=context)

    def test_visitor_cannot_upsert(self):
        user = factories.User()
        config.authorized_users = [user["name"]]
        context = dict(user="127.0.0.1", model=model)
        nose.tools.assert_raises(toolkit.NotAuthorized,
                                 custom_helpers.call_auth,
                                 "ckanext_deadoralive_upsert", context=context)
