"""Tests for auth/get.py."""
import nose.tools

import ckan.model as model
import ckan.new_tests.factories as factories
import ckan.plugins.toolkit as toolkit
import ckanext.deadoralive.config as config
import ckanext.deadoralive.tests.helpers as custom_helpers
import ckanext.deadoralive.tests.factories as custom_factories


class TestGet(custom_helpers.FunctionalTestBaseClass):

    def test_configured_users_can_get_resource_ids(self):
        user = factories.User()
        config.authorized_users = [user["name"]]
        context = dict(user=user["name"], model=model)
        assert custom_helpers.call_auth(
            "ckanext_deadoralive_get_resources_to_check",
            context=context) is True

    def test_other_users_cannot_get_resource_ids(self):
        user_1 = factories.User()
        user_2 = factories.User()
        config.authorized_users = [user_1["name"]]
        context = dict(user=user_2["name"], model=model)
        nose.tools.assert_raises(toolkit.NotAuthorized,
                                 custom_helpers.call_auth,
                                 "ckanext_deadoralive_get_resources_to_check",
                                 context=context)

    def test_visitor_cannot_get_resource_ids(self):
        user = factories.User()
        config.authorized_users = [user["name"]]
        context = dict(user="127.0.0.1", model=model)
        nose.tools.assert_raises(toolkit.NotAuthorized,
                                 custom_helpers.call_auth,
                                 "ckanext_deadoralive_get_resources_to_check",
                                 context=context)

    def test_anyone_can_get(self):
        user_1 = factories.User()
        user_2 = factories.User()
        config.authorized_users = [user_1["name"]]

        for user in (user_1["name"], user_2["name"], '127.0.0.1'):
            context = dict(user=user, model=model)
            assert custom_helpers.call_auth(
                "ckanext_deadoralive_get", context=context) is True

    def test_anyone_can_get_broken_links_report(self):
        user_1 = factories.User()
        user_2 = factories.User()
        config.authorized_users = [user_1["name"]]

        for user in (user_1["name"], user_2["name"], '127.0.0.1'):
            context = dict(user=user, model=model)
            assert custom_helpers.call_auth(
                "ckanext_deadoralive_broken_links_by_organization",
                context=context) is True

    def test_non_sysadmins_cannot_get_broken_links_by_email_report(self):
        user_1 = factories.User()
        user_2 = factories.User()
        config.authorized_users = [user_1["name"]]

        for user in (user_1["name"], user_2["name"], '127.0.0.1'):
            context = dict(user=user, model=model)
            nose.tools.assert_raises(
                toolkit.NotAuthorized, custom_helpers.call_auth,
                "ckanext_deadoralive_broken_links_by_email",
                context=context)

    def test_sysadmins_can_get_broken_links_by_email_report(self):
        sysadmin = custom_factories.Sysadmin()
        config.authorized_users = []
        context = dict(user=sysadmin["name"], model=model)

        assert custom_helpers.call_auth(
            "ckanext_deadoralive_broken_links_by_email",
            context=context) is True
