"""Frontend tests for controllers.py."""
import datetime

import ckan.new_tests.factories as factories
import ckanext.deadoralive.tests.helpers as custom_helpers
import ckanext.deadoralive.tests.factories as custom_factories
import ckanext.deadoralive.logic.action.update as update


class TestBrokenLinksController(custom_helpers.FunctionalTestBaseClass):

    def test_broken_links_by_organization(self):

        user = factories.User()
        context = {'user': user['name']}

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

        # Make these resources have broken links.
        for resource in (resource_1, resource_3, resource_4, resource_5,
                         resource_6, resource_7):
            one_day_ago = datetime.datetime.now() - datetime.timedelta(days=1)
            four_days_ago = datetime.datetime.now() - datetime.timedelta(days=4)
            seven_days_ago = datetime.datetime.now() - datetime.timedelta(
                days=7)
            data_dict = dict(
                resource_id=resource["id"],
                alive=False,
            )
            update.upsert(context=context, data_dict=data_dict,
                          last_checked=one_day_ago)
            update.upsert(context=context, data_dict=data_dict,
                          last_checked=four_days_ago)
            update.upsert(context=context, data_dict=data_dict,
                          last_checked=seven_days_ago)

        # Make these resources have working links.
        for resource in (resource_2, resource_8):
            data_dict = dict(
                resource_id=resource["id"],
                alive=True,
            )
            update.upsert(context=context, data_dict=data_dict)

        response = self.app.get("/broken_links")

        assert org_1["name"] in response
        assert org_2["name"] in response
        assert org_3["name"] in response
        assert dataset_1["name"] in response
        assert dataset_2["name"] not in response
        assert dataset_3["name"] in response
        assert dataset_4["name"] in response
        assert dataset_5["name"] in response
