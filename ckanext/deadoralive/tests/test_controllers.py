# -*- coding: utf-8 -*-
"""Frontend tests for controllers.py."""
import ckan.new_tests.factories as factories
import ckanext.deadoralive.tests.helpers as custom_helpers
import ckanext.deadoralive.tests.factories as custom_factories
import ckanext.deadoralive.config as config


class TestBrokenLinksController(custom_helpers.FunctionalTestBaseClass):

    def test_broken_links_by_organization(self):
        user = factories.User()
        config.authorized_users = [user["name"]]

        org_1 = factories.Organization()
        dataset_1 = custom_factories.Dataset(owner_org=org_1["id"])
        dataset_2 = custom_factories.Dataset(owner_org=org_1["id"])
        resource_1 = custom_factories.Resource(package_id=dataset_1["id"])
        resource_2 = custom_factories.Resource(package_id=dataset_2["id"])

        org_2 = factories.Organization()
        dataset_3 = custom_factories.Dataset(owner_org=org_2["id"])
        resource_3 = custom_factories.Resource(package_id=dataset_3["id"])
        resource_4 = custom_factories.Resource(package_id=dataset_3["id"])

        org_3 = factories.Organization()
        dataset_4 = custom_factories.Dataset(owner_org=org_3["id"])
        resource_5 = custom_factories.Resource(package_id=dataset_4["id"])
        dataset_5 = custom_factories.Dataset(owner_org=org_3["id"])
        resource_6 = custom_factories.Resource(package_id=dataset_5["id"])
        resource_7 = custom_factories.Resource(package_id=dataset_5["id"])
        resource_8 = custom_factories.Resource(package_id=dataset_5["id"])

        custom_helpers.make_broken((resource_1, resource_3, resource_4,
                                    resource_5, resource_6, resource_7),
                                   user=user)
        custom_helpers.make_working((resource_2, resource_8), user=user)

        response = self.app.get("/organization/broken_links")

        assert org_1["name"] in response
        assert org_2["name"] in response
        assert org_3["name"] in response
        assert dataset_1["name"] in response
        assert dataset_2["name"] not in response
        assert dataset_3["name"] in response
        assert dataset_4["name"] in response
        assert dataset_5["name"] in response

    def test_broken_links_by_organization_when_no_broken_links(self):
        response = self.app.get("/organization/broken_links")
        assert "This site has no broken links" in response

    def test_broken_links_by_organization_with_unicode(self):
        user = factories.User()
        config.authorized_users = [user["name"]]

        org = factories.Organization(title=u"Test Örganißation")
        dataset = custom_factories.Dataset(owner_org=org["id"],
                                           title=u"Test Dätaßet")
        resource = custom_factories.Resource(package_id=dataset["id"],
                                             name=u"Test Rëßource",
                                             url=u"http://bröken_link")

        custom_helpers.make_broken((resource,), user=user)

        self.app.get("/organization/broken_links")

    def test_broken_links_by_email(self):
        sysadmin = custom_factories.Sysadmin()
        extra_environ = {'REMOTE_USER': str(sysadmin["name"])}

        maintainer_1 = "maintainer_1@maintainers.com"
        dataset_1 = custom_factories.Dataset(
            maintainer_email=maintainer_1)
        resource_1 = custom_factories.Resource(package_id=dataset_1["id"])
        dataset_2 = custom_factories.Dataset(
            maintainer_email=maintainer_1)
        resource_2 = custom_factories.Resource(package_id=dataset_2["id"])

        maintainer_2 = "maintainer_2@maintainers.com"
        dataset_3 = custom_factories.Dataset(
            maintainer_email=maintainer_2)
        resource_3 = custom_factories.Resource(package_id=dataset_3["id"])
        resource_4 = custom_factories.Resource(package_id=dataset_3["id"])

        maintainer_3 = "maintainer_3@maintainers.com"
        dataset_4 = custom_factories.Dataset(
            maintainer_email=maintainer_3)
        resource_5 = custom_factories.Resource(package_id=dataset_4["id"])
        dataset_5 = custom_factories.Dataset(
            maintainer_email=maintainer_3)
        resource_6 = custom_factories.Resource(package_id=dataset_5["id"])
        resource_7 = custom_factories.Resource(package_id=dataset_5["id"])
        resource_8 = custom_factories.Resource(package_id=dataset_5["id"])

        custom_helpers.make_broken((resource_1, resource_3, resource_4,
                                    resource_5, resource_6, resource_7),
                                   user=sysadmin)
        custom_helpers.make_working((resource_2, resource_8), user=sysadmin)

        response = self.app.get("/ckan-admin/broken_links",
                                extra_environ=extra_environ)

        assert maintainer_1 in response
        assert maintainer_2 in response
        assert maintainer_3 in response
        assert dataset_1["name"] in response
        assert dataset_2["name"] not in response
        assert dataset_3["name"] in response
        assert dataset_4["name"] in response
        assert dataset_5["name"] in response

    def test_broken_links_by_email_not_authorized(self):
        """Non-sysadmins should get redirected if they try to get the page."""
        user = factories.User()
        for extra_environ in (None, {'REMOTE_USER': str(user["name"])}):
            self.app.get("/ckan-admin/broken_links", status=302)

    def test_broken_links_by_email_when_no_broken_links(self):
        sysadmin = custom_factories.Sysadmin()
        extra_environ = {'REMOTE_USER': str(sysadmin["name"])}

        response = self.app.get("/ckan-admin/broken_links",
                                extra_environ=extra_environ)

        assert "This site has no broken links" in response

    def test_broken_links_by_email_with_unicode(self):
        sysadmin = custom_factories.Sysadmin()
        extra_environ = {'REMOTE_USER': str(sysadmin["name"])}
        maintainer = u"Mäintainer"
        maintainer_email = u"mäintainer@maintainers.com"
        author = u"Aüthör"
        author_email = u"aüthör@authors.com"
        dataset_1 = custom_factories.Dataset(
            title=u"Test Dätaßet", maintainer=maintainer,
            maintainer_email=maintainer_email)
        dataset_2 = custom_factories.Dataset(
            title=u"Test Dätaßet", author=author, author_email=author_email)
        resource_1 = custom_factories.Resource(package_id=dataset_1["id"],
                                               name=u"Test Rësourße",
                                               url=u"http://bröken_link")
        resource_2 = custom_factories.Resource(package_id=dataset_2["id"],
                                               name=u"Test Rësourße",
                                               url=u"http://bröken_link")

        custom_helpers.make_broken((resource_1, resource_2), user=sysadmin)

        self.app.get("/ckan-admin/broken_links", extra_environ=extra_environ)
