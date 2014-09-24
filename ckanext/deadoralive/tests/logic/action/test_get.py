"""Tests for logic/action/get.py."""
import datetime

import ckan.new_tests.helpers as helpers
import ckanext.deadoralive.tests.helpers as custom_helpers
import ckan.new_tests.factories as factories
import ckanext.deadoralive.tests.factories as custom_factories
import ckanext.deadoralive.logic.action.get as get
import ckanext.deadoralive.config as config


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
                                   user)
        custom_helpers.make_working((resource_2, resource_8), user)

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


class TestBrokenLinksByEmail(custom_helpers.FunctionalTestBaseClass):
    """Tests for the broken_links_by_email() API action."""

    def test_with_no_datasets(self):
        """When there are no datasets or resources it should return []."""
        result = helpers.call_action(
            "ckanext_deadoralive_broken_links_by_email")
        assert result == []

    def test_dataset_with_no_resources(self):
        """A dataset with no resources shouldn't show up in the report."""
        custom_factories.Dataset()
        result = helpers.call_action(
            "ckanext_deadoralive_broken_links_by_email")
        assert result == []

    def test_dataset_with_no_broken_resources(self):
        """A dataset with no broken resources shouldn't be in the report."""
        dataset = custom_factories.Dataset()
        custom_factories.Resource(package_id=dataset["id"])
        result = helpers.call_action(
            "ckanext_deadoralive_broken_links_by_email")
        assert result == []

    def test_dataset_with_no_email(self):
        """Datasets with no email should get email: None.

        All datasets that have broken links but no maintainer or author email
        should be grouped into a single email: None dict in the report.

        """
        user = factories.User()
        config.authorized_users = [user["name"]]

        # Create 3 datasets with no authors or maintainers.
        dataset_1 = custom_factories.Dataset()
        dataset_2 = custom_factories.Dataset()
        dataset_3 = custom_factories.Dataset()

        # Each of the datasets needs to have a resource with a broken link,
        # so that they show up in the report.
        resource_1 = custom_factories.Resource(package_id=dataset_1["id"])
        resource_2 = custom_factories.Resource(package_id=dataset_2["id"])
        resource_3 = custom_factories.Resource(package_id=dataset_3["id"])
        custom_helpers.make_broken((resource_1, resource_2, resource_3),
                                   user=user)

        result = helpers.call_action(
            "ckanext_deadoralive_broken_links_by_email")

        assert len(result) == 1
        result = result[0]

        assert result["email"] is None
        assert result["num_broken_links"] == 3

        datasets = result["datasets_with_broken_links"]
        assert len(datasets) == 3

        dataset_names = [dataset["name"] for dataset in datasets]
        for dataset in (dataset_1, dataset_2, dataset_3):
            assert dataset["name"] in dataset_names

    def test_mailto_url_with_one_broken_link(self):
        """Test that the mailto: URLs are formed correctly when one broken link.

        """
        user = factories.User()
        config.authorized_users = [user["name"]]

        dataset = custom_factories.Dataset(
            maintainer_email="test_maintainer@test.com")
        resource_1 = custom_factories.Resource(package_id=dataset["id"])
        resource_2 = custom_factories.Resource(package_id=dataset["id"])
        resource_3 = custom_factories.Resource(package_id=dataset["id"])
        custom_helpers.make_broken((resource_1, resource_2, resource_3), user)

        result = helpers.call_action(
            "ckanext_deadoralive_broken_links_by_email")

        assert len(result) == 1
        result = result[0]

        subject = "You have a dataset with broken links on CKAN"
        body = "This dataset contains a broken link:%0A%0A{title}%0A{url}"
        url = "http://test.ckan.net/dataset/" + dataset["name"]
        body = body.format(title=dataset["title"], url=url)
        expected_mailto = "mailto:{email}?subject={subject}&body={body}".format(
            email=dataset["maintainer_email"], subject=subject, body=body)
        assert result["mailto"] == expected_mailto

    def test_mailto_url_with_many_broken_links(self):
        """Test the mailto: URLs with many broken links.

        Test that the mailto: URLs are formed correctly when a maintainer has
        many datasets with broken links.

        """
        user = factories.User()
        config.authorized_users = [user["name"]]

        dataset_1 = custom_factories.Dataset(
            maintainer_email="test_maintainer@test.com")
        resource_1 = custom_factories.Resource(package_id=dataset_1["id"])
        dataset_2 = custom_factories.Dataset(
            maintainer_email="test_maintainer@test.com")
        resource_2 = custom_factories.Resource(package_id=dataset_2["id"])
        dataset_3 = custom_factories.Dataset(
            maintainer_email="test_maintainer@test.com")
        resource_3 = custom_factories.Resource(package_id=dataset_3["id"])
        custom_helpers.make_broken((resource_1, resource_2, resource_3),
                                   user)

        result = helpers.call_action(
            "ckanext_deadoralive_broken_links_by_email")

        assert len(result) == 1
        result = result[0]

        subject = "You have 3 datasets with broken links on CKAN"
        body = "These datasets have broken links:"
        for dataset in (dataset_3, dataset_2, dataset_1):
            url = "http://test.ckan.net/dataset/" + dataset["name"]
            body += "%0A%0A{title}%0A{url}".format(
                title=dataset["title"], url=url)
        expected_mailto = "mailto:{email}?subject={subject}&body={body}".format(
            email=dataset["maintainer_email"], subject=subject, body=body)
        assert result["mailto"] == expected_mailto

    def test_mix_of_broken_and_working_links(self):
        user = factories.User()
        config.authorized_users = [user["name"]]

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
                                    resource_5, resource_6, resource_7), user)
        custom_helpers.make_working((resource_2, resource_8), user)

        report = helpers.call_action(
            "ckanext_deadoralive_broken_links_by_email")

        assert len(report) == 3, ("There should be 3 emails listed in the "
                                  "report")

        assert [item["email"] for item in report] == [
            maintainer_3, maintainer_2, maintainer_1], (
                "The items should be sorted most broken datasets first")

        # Check that the num_broken_links for each item is correct.
        assert report[0]["num_broken_links"] == 3
        assert report[1]["num_broken_links"] == 2
        assert report[2]["num_broken_links"] == 1

        # Check maintainer_3's report in detail.
        maintainer_3_report = report[0]
        assert len(maintainer_3_report["datasets_with_broken_links"]) == 2
        broken_datasets = maintainer_3_report["datasets_with_broken_links"]
        assert [dataset["name"] for dataset in broken_datasets] == [
            dataset_5["name"], dataset_4["name"]]
        dataset_5_report = broken_datasets[0]
        assert dataset_5_report["num_broken_links"] == 2
        assert len(dataset_5_report["resources_with_broken_links"]) == 2
        assert [resource_id for resource_id
                in dataset_5_report["resources_with_broken_links"]] == [
                    resource_6["id"], resource_7["id"]]
