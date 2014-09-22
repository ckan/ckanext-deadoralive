"""Tests for logic/action/get.py."""
import datetime

import ckan.new_tests.helpers as helpers
import ckanext.deadoralive.tests.helpers as custom_helpers
import ckan.new_tests.factories as factories
import ckanext.deadoralive.tests.factories as custom_factories
import ckanext.deadoralive.logic.action.get as get
import ckanext.deadoralive.logic.action.update as update


class TestGetResourcesToCheck(custom_helpers.FunctionalTestBaseClass):
    """Tests for the get_resources_to_check() action function.

    The details of which resources are returned is tested in the model tests,
    here we just test the stuff that the action function itself does.

    """
    def test_get_resources_to_check(self):
        """Simple test: call get_resources_to_check() and test the result."""
        custom_factories.Resource()
        custom_factories.Resource()
        custom_factories.Resource()

        resource_ids = helpers.call_action(
            "ckanext_deadoralive_get_resources_to_check")

        assert len(resource_ids) == 3

    # TODO: Test config setting reading and defaults, test that they get
    #       passed to model.
    # TODO: Test invalid config setting (move config setting parsing into its
    #       own function)
    # TODO: Test n param.
    # TODO: Test validation.


class TestBrokenLinksByOrganization(custom_helpers.FunctionalTestBaseClass):

    def test_when_there_are_no_organizations(self):

        def organization_list(context=None, data_dict=None):
            return []

        def all_results():
            return []

        def package_search(*args, **kwargs):
            return []

        report = get._broken_links_by_organization(
            None, organization_list, all_results, package_search)

        assert report == []

    def test_with_org_with_no_datasets(self):

        def organization_list(context=None, data_dict=None):
            return ["test_org"]

        def all_results():
            return []

        def package_search(*args, **kwargs):
            return []

        report = get._broken_links_by_organization(
            None, organization_list, all_results, package_search)

        assert report == [{"name": "test_org",
                           "num_broken_links": 0,
                           "datasets_with_broken_links": [],
                           }]

    def test_with_dataset_with_no_resources(self):

        def organization_list(context=None, data_dict=None):
            return ["test_org"]

        def all_results():
            return []

        def package_search(*args, **kwargs):
            return [
                {"name": "test_dataset",
                 "resources": [],
                 },
            ]

        report = get._broken_links_by_organization(
            None, organization_list, all_results, package_search)

        assert report == [{"name": "test_org",
                           "num_broken_links": 0,
                           "datasets_with_broken_links": [],
                           }]

    def test_organization_with_no_broken_links(self):

        def organization_list(context=None, data_dict=None):
            return ["test_org"]

        def all_results():
            now = datetime.datetime.now().isoformat()
            results = []
            for i in range(1, 10):
                results.append({
                    "resource_id": "test_resource_{0}".format(i),
                    "alive": True,
                    "last_checked": now,
                    "last_successful": now,
                    "num_fails": 0,
                    "pending": False,
                    "pending_since": None,
                    "status": None,
                    "reason": None,
                })
            return results

        def package_search(*args, **kwargs):
            return [
                {"name": "test_dataset_1",
                 "resources": [
                     {"id": "test_resource_1"},
                     {"id": "test_resource_2"},
                     {"id": "test_resource_3"}
                 ]},
                {"name": "test_dataset_2",
                 "resources": [
                     {"id": "test_resource_4"},
                     {"id": "test_resource_5"},
                     {"id": "test_resource_6"}
                 ]},
                {"name": "test_dataset_3",
                 "resources": [
                     {"id": "test_resource_7"},
                     {"id": "test_resource_8"},
                     {"id": "test_resource_9"}
                 ]}
            ]

        report = get._broken_links_by_organization(
            None, organization_list, all_results, package_search)

        assert report == [{"name": "test_org",
                           "num_broken_links": 0,
                           "datasets_with_broken_links": [],
                           }]

    def test_mix_of_broken_and_working_links(self):

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

        report = helpers.call_action(
            "ckanext_deadoralive_broken_links_by_organization")

        assert len(report) == 3, ("There should be 3 organizations listed in "
                                  "the report")

        assert [org["name"] for org in report] == [
            org_3["name"], org_2["name"], org_1["name"]], (
                "The organizations should be sorted most broken datasets first")

        # Check that the num_broken_links for each org is correct.
        assert report[0]["num_broken_links"] == 3
        assert report[1]["num_broken_links"] == 2
        assert report[2]["num_broken_links"] == 1

        # Check org_3's report in detail.
        org_3_report = report[0]
        assert len(org_3_report["datasets_with_broken_links"]) == 2
        org_3_broken_datasets = org_3_report["datasets_with_broken_links"]
        assert [dataset["name"] for dataset in org_3_broken_datasets] == [
            dataset_5["name"], dataset_4["name"]]
        dataset_5_report = org_3_broken_datasets[0]
        assert dataset_5_report["num_broken_links"] == 2
        assert len(dataset_5_report["resources_with_broken_links"]) == 2
        assert [resource_id for resource_id
                in dataset_5_report["resources_with_broken_links"]] == [
                    resource_6["id"], resource_7["id"]]
