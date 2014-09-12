"""Tests for model/link_checker_results.py."""
import datetime
import ckan.new_tests.helpers as helpers
import ckan.new_tests.factories as factories

import ckanext.deadoralive.model.link_checker_results as link_checker_results


class TestSaveLinkCheckerResult(object):
    """Tests for the save_link_checker_result() function.

    These also test the get_link_checker_results() function.

    """
    def setup(self):
        helpers.reset_db()
        link_checker_results.create_link_checker_results_table()

    def test_save_and_retrieve_good_link(self):
        before = datetime.datetime.utcnow()
        link_checker_results.save_link_checker_result("test_resource_id", True)
        after = datetime.datetime.utcnow()
        results = link_checker_results.get_link_checker_results(
            "test_resource_id")
        assert len(results) == 1
        result = results[0]
        assert result["resource_id"] == "test_resource_id"
        assert result["alive"] is True
        assert result["datetime"] > before
        assert result["datetime"] < after

    def test_save_and_retrieve_broken_link(self):
        before = datetime.datetime.utcnow()
        link_checker_results.save_link_checker_result("test_resource_id", False)
        after = datetime.datetime.utcnow()
        results = link_checker_results.get_link_checker_results(
            "test_resource_id")
        assert len(results) == 1
        result = results[0]
        assert result["resource_id"] == "test_resource_id"
        assert result["alive"] is False
        assert result["datetime"] > before
        assert result["datetime"] < after

    def test_save_and_retrieve_pending_result(self):
        before = datetime.datetime.utcnow()
        link_checker_results.save_link_checker_result("test_resource_id", None)
        after = datetime.datetime.utcnow()
        results = link_checker_results.get_link_checker_results(
            "test_resource_id")
        assert len(results) == 1
        result = results[0]
        assert result["resource_id"] == "test_resource_id"
        assert result["alive"] is None
        assert result["datetime"] > before
        assert result["datetime"] < after

    def test_save_and_retrieve_multiple(self):
        for i in range(0, 10):
            link_checker_results.save_link_checker_result("test_resource_id",
                                                          False)
        results = link_checker_results.get_link_checker_results(
            "test_resource_id")

        assert len(results) == 10
        for result in results:
            assert result["resource_id"] == "test_resource_id"
            assert result["alive"] is False

    def test_save_with_custom_datetime(self):
        custom_time = datetime.datetime.utcnow() - datetime.timedelta(days=500,
                                                                      hours=12)
        link_checker_results.save_link_checker_result("test_resource_id", True,
                                                      custom_time)
        results = link_checker_results.get_link_checker_results(
            "test_resource_id")
        assert len(results) == 1
        result = results[0]
        assert result["resource_id"] == "test_resource_id"
        assert result["alive"] is True
        assert result["datetime"] == custom_time

    def test_that_only_results_for_the_requested_resource_are_returned(self):
        # Save some good, bad and pending results for some other resources.
        link_checker_results.save_link_checker_result("other_resource_1", True)
        link_checker_results.save_link_checker_result("other_resource_2", None)
        link_checker_results.save_link_checker_result("other_resource_3", False)
        link_checker_results.save_link_checker_result("other_resource_3", False)
        link_checker_results.save_link_checker_result("other_resource_3", False)
        link_checker_results.save_link_checker_result("test_resource", False)
        link_checker_results.save_link_checker_result("test_resource", False)

        results = link_checker_results.get_link_checker_results("test_resource")
        assert len(results) == 2
        for result in results:
            assert result["resource_id"] == "test_resource"
            assert result["alive"] is False

    def test_that_old_results_are_deleted(self):
        """Results > 1 week old should be deleted when a new result is saved.

        All old results should be deleted: good, bad and pending ones, for any
        resource.

        """
        two_weeks_ago = datetime.datetime.utcnow() - datetime.timedelta(weeks=1)

        # Create some old results.
        link_checker_results.save_link_checker_result("other_resource_1", True,
                                                      two_weeks_ago)
        link_checker_results.save_link_checker_result("other_resource_2", None,
                                                      two_weeks_ago)
        link_checker_results.save_link_checker_result("other_resource_3", False,
                                                      two_weeks_ago)
        link_checker_results.save_link_checker_result("other_resource_3", False,
                                                      two_weeks_ago)
        link_checker_results.save_link_checker_result("other_resource_3", False,
                                                      two_weeks_ago)
        link_checker_results.save_link_checker_result("test_resource", False,
                                                      two_weeks_ago)
        link_checker_results.save_link_checker_result("test_resource", False,
                                                      two_weeks_ago)

        # Now create a new result.
        link_checker_results.save_link_checker_result("test_resource", False)

        for resource_id in ("other_resource_1", "other_resource_2",
                            "other_resource_3"):
            results = link_checker_results.get_link_checker_results(resource_id)
            assert results == []

        results = link_checker_results.get_link_checker_results("test_resource")
        assert len(results) == 1


class TestGetResourcesToCheck(object):
    """Tests for the get_resources_to_check() function."""

    def setup(self):
        helpers.reset_db()
        link_checker_results.create_link_checker_results_table()

    def test_with_5_new_resources_and_request_10(self):
        """
        If there are 5 new resources (that have never been checked before) and
        10 resources to check are requested, the 5 should be returned in
        oldest-first order.

        """
        resource_1 = factories.Resource()['id']
        resource_2 = factories.Resource()['id']
        resource_3 = factories.Resource()['id']
        resource_4 = factories.Resource()['id']
        resource_5 = factories.Resource()['id']

        resources_to_check = link_checker_results.get_resources_to_check(10)

        assert resources_to_check == [resource_1, resource_2, resource_3,
                                      resource_4, resource_5]

    def test_with_10_new_resources_and_request_5(self):
        """
        If there are 10 new resources (that have never been checked before) and
        5 resources to check are requested, the oldest 5 should be returned in
        oldest-first order.

        """
        resource_1 = factories.Resource()['id']
        resource_2 = factories.Resource()['id']
        resource_3 = factories.Resource()['id']
        resource_4 = factories.Resource()['id']
        resource_5 = factories.Resource()['id']
        factories.Resource()['id']
        factories.Resource()['id']
        factories.Resource()['id']
        factories.Resource()['id']
        factories.Resource()['id']

        resources_to_check = link_checker_results.get_resources_to_check(5)

        assert resources_to_check == [resource_1, resource_2, resource_3,
                                      resource_4, resource_5]

    def test_when_all_resources_have_been_checked_recently(self):
        """

        If there are 5 resources and they have all been checked in last 24 hours
        then it should return an empty list.

        """
        resource_1 = factories.Resource()['id']
        resource_2 = factories.Resource()['id']
        resource_3 = factories.Resource()['id']
        resource_4 = factories.Resource()['id']
        resource_5 = factories.Resource()['id']
        twenty_hours_ago = datetime.datetime.utcnow() - datetime.timedelta(
            hours=23)
        link_checker_results.save_link_checker_result(resource_1, True,
                                                      twenty_hours_ago)
        link_checker_results.save_link_checker_result(resource_2, True,
                                                      twenty_hours_ago)
        link_checker_results.save_link_checker_result(resource_3, True,
                                                      twenty_hours_ago)
        link_checker_results.save_link_checker_result(resource_4, True,
                                                      twenty_hours_ago)
        link_checker_results.save_link_checker_result(resource_5, True,
                                                      twenty_hours_ago)

        resources_to_check = link_checker_results.get_resources_to_check(10)

        assert resources_to_check == []

    def test_with_some_resources_checked_recently_and_some_never(self):
        """

        If there are 5 resources that have been checked in last 24 hours and 5
        that have never been checked and 10 resources are requested, it should
        return the 5 that have not been checked, sorted oldest-resource-first.

        """
        resource_1 = factories.Resource()['id']
        resource_2 = factories.Resource()['id']
        resource_3 = factories.Resource()['id']
        resource_4 = factories.Resource()['id']
        resource_5 = factories.Resource()['id']
        twenty_hours_ago = datetime.datetime.utcnow() - datetime.timedelta(
            hours=23)
        link_checker_results.save_link_checker_result(resource_1, True,
                                                      twenty_hours_ago)
        link_checker_results.save_link_checker_result(resource_2, True,
                                                      twenty_hours_ago)
        link_checker_results.save_link_checker_result(resource_3, True,
                                                      twenty_hours_ago)
        link_checker_results.save_link_checker_result(resource_4, True,
                                                      twenty_hours_ago)
        link_checker_results.save_link_checker_result(resource_5, True,
                                                      twenty_hours_ago)
        resource_6 = factories.Resource()['id']
        resource_7 = factories.Resource()['id']
        resource_8 = factories.Resource()['id']
        resource_9 = factories.Resource()['id']
        resource_10 = factories.Resource()['id']

        resources_to_check = link_checker_results.get_resources_to_check(10)

        assert resources_to_check == [resource_6, resource_7, resource_8,
                                      resource_9, resource_10]

    def test_with_some_resources_checked_recently_and_some_not_recently(self):
        """

        If there are 5 resources that have been checked in last 24 hours and 5
        that were last checked more than 24 hours ago and 10 resources are
        requested, it should return the 5 that have not been checked recently,
        sorted most-recently-checked last.

        """
        now = datetime.datetime.utcnow()
        resource_1 = factories.Resource()['id']
        resource_2 = factories.Resource()['id']
        resource_3 = factories.Resource()['id']
        resource_4 = factories.Resource()['id']
        resource_5 = factories.Resource()['id']
        twenty_hours_ago = now - datetime.timedelta(hours=23)
        link_checker_results.save_link_checker_result(resource_1, True,
                                                      twenty_hours_ago)
        link_checker_results.save_link_checker_result(resource_2, True,
                                                      twenty_hours_ago)
        link_checker_results.save_link_checker_result(resource_3, True,
                                                      twenty_hours_ago)
        link_checker_results.save_link_checker_result(resource_4, True,
                                                      twenty_hours_ago)
        link_checker_results.save_link_checker_result(resource_5, True,
                                                      twenty_hours_ago)
        resource_6 = factories.Resource()['id']
        resource_7 = factories.Resource()['id']
        resource_8 = factories.Resource()['id']
        resource_9 = factories.Resource()['id']
        resource_10 = factories.Resource()['id']
        # We mix up the order in which these resources were checked a bit.
        link_checker_results.save_link_checker_result(
            resource_7, True, now - datetime.timedelta(hours=34))
        link_checker_results.save_link_checker_result(
            resource_6, True, now - datetime.timedelta(hours=33))
        link_checker_results.save_link_checker_result(
            resource_9, True, now - datetime.timedelta(hours=32))
        link_checker_results.save_link_checker_result(
            resource_10, True, now - datetime.timedelta(hours=31))
        link_checker_results.save_link_checker_result(
            resource_8, True, now - datetime.timedelta(hours=30))

        resources_to_check = link_checker_results.get_resources_to_check(10)

        assert resources_to_check == [resource_7, resource_6, resource_9,
                                      resource_10, resource_8]

    def test_that_it_does_not_return_resources_with_pending_checks(self):
        """Resources with pending checks < 2 hours old should not be returned.

        """
        now = datetime.datetime.utcnow()

        # Create 5 resources that have been checked in the last 24 hours.
        resource_1 = factories.Resource()['id']
        resource_2 = factories.Resource()['id']
        resource_3 = factories.Resource()['id']
        resource_4 = factories.Resource()['id']
        resource_5 = factories.Resource()['id']
        twenty_hours_ago = now - datetime.timedelta(hours=20)
        link_checker_results.save_link_checker_result(resource_1, True,
                                                      twenty_hours_ago)
        link_checker_results.save_link_checker_result(resource_2, True,
                                                      twenty_hours_ago)
        link_checker_results.save_link_checker_result(resource_3, True,
                                                      twenty_hours_ago)
        link_checker_results.save_link_checker_result(resource_4, True,
                                                      twenty_hours_ago)
        link_checker_results.save_link_checker_result(resource_5, True,
                                                      twenty_hours_ago)

        # Create 5 resources with pending checks from < 2 hours ago.
        resource_6 = factories.Resource()['id']
        resource_7 = factories.Resource()['id']
        resource_8 = factories.Resource()['id']
        resource_9 = factories.Resource()['id']
        resource_10 = factories.Resource()['id']
        one_hour_ago = now - datetime.timedelta(hours=1)
        link_checker_results.save_link_checker_result(resource_6, None,
                                                      one_hour_ago)
        link_checker_results.save_link_checker_result(resource_7, None,
                                                      one_hour_ago)
        link_checker_results.save_link_checker_result(resource_8, None,
                                                      one_hour_ago)
        link_checker_results.save_link_checker_result(resource_9, None,
                                                      one_hour_ago)
        link_checker_results.save_link_checker_result(resource_10, None,
                                                      one_hour_ago)

        # Create 5 resources that were last checked more than 24 hours ago.
        resource_11 = factories.Resource()['id']
        resource_12 = factories.Resource()['id']
        resource_13 = factories.Resource()['id']
        resource_14 = factories.Resource()['id']
        resource_15 = factories.Resource()['id']
        thirty_hours_ago = now - datetime.timedelta(hours=30)
        link_checker_results.save_link_checker_result(resource_11, True,
                                                      thirty_hours_ago)
        link_checker_results.save_link_checker_result(resource_12, True,
                                                      thirty_hours_ago)
        link_checker_results.save_link_checker_result(resource_13, True,
                                                      thirty_hours_ago)
        link_checker_results.save_link_checker_result(resource_14, True,
                                                      thirty_hours_ago)
        link_checker_results.save_link_checker_result(resource_15, True,
                                                      thirty_hours_ago)

        resources_to_check = link_checker_results.get_resources_to_check(10)

        assert resources_to_check == [resource_11, resource_12, resource_13,
                                      resource_14, resource_15]

    def test_that_it_does_return_resources_with_expired_pending_checks(self):
        """Resources with pending checks > 2 hours old should be returned.

        And they should be sorted oldest-pending-check-first.

        """
        # Create 5 resources with pending checks from > 2 hours ago.
        resource_1 = factories.Resource()['id']
        resource_2 = factories.Resource()['id']
        resource_3 = factories.Resource()['id']
        resource_4 = factories.Resource()['id']
        resource_5 = factories.Resource()['id']
        five_hours_ago = datetime.datetime.utcnow() - datetime.timedelta(
            hours=5)
        # Mix up the ordering of the checks here.
        link_checker_results.save_link_checker_result(resource_5, None,
                                                      five_hours_ago)
        link_checker_results.save_link_checker_result(resource_2, None,
                                                      five_hours_ago)
        link_checker_results.save_link_checker_result(resource_4, None,
                                                      five_hours_ago)
        link_checker_results.save_link_checker_result(resource_3, None,
                                                      five_hours_ago)
        link_checker_results.save_link_checker_result(resource_1, None,
                                                      five_hours_ago)

        resources_to_check = link_checker_results.get_resources_to_check(10)

        assert resources_to_check == [resource_5, resource_2, resource_4,
                                      resource_3, resource_1]

    def test_that_it_creates_pending_checks(self):
        """get_resources_to_check() should create pending link checker results
        for all the resources it returns."""

        # A resource that has never been checked.
        resource_1 = factories.Resource()['id']

        # A resource that was checked > 24 hours ago.
        resource_2 = factories.Resource()['id']
        thirty_hours_ago = datetime.datetime.utcnow() - datetime.timedelta(
            hours=30)
        link_checker_results.save_link_checker_result(resource_2, True,
                                                      thirty_hours_ago)

        # A resource with a pending check from > 2 hours ago.
        resource_3 = factories.Resource()['id']
        three_hours_ago = datetime.datetime.utcnow() - datetime.timedelta(
            hours=3)
        link_checker_results.save_link_checker_result(resource_3, None,
                                                      three_hours_ago)

        before = datetime.datetime.utcnow()

        link_checker_results.get_resources_to_check(10)

        for resource in (resource_1, resource_2, resource_3):
            result = link_checker_results.get_link_checker_results(resource)[-1]
            assert result["alive"] is None
            assert result["datetime"] > before

    def test_custom_shorter_since(self):
        """If given a shorter ``since`` time it should return resources that
        have been checked more recently."""
        test_resource = factories.Resource()['id']
        ten_hours_ago = datetime.datetime.utcnow() - datetime.timedelta(
            hours=10)
        link_checker_results.save_link_checker_result(test_resource, True,
                                                      ten_hours_ago)

        results = link_checker_results.get_resources_to_check(
            10, since=datetime.timedelta(hours=5))

        assert len(results) == 1
        assert results[0] == test_resource

    def test_custom_longer_since(self):
        """If given a longer ``since`` time it should not return resources that
        were checked more recently."""
        test_resource = factories.Resource()['id']
        thirty_hours_ago = datetime.datetime.utcnow() - datetime.timedelta(
            hours=30)
        link_checker_results.save_link_checker_result(test_resource, True,
                                                      thirty_hours_ago)

        results = link_checker_results.get_resources_to_check(
            10, since=datetime.timedelta(hours=48))

        assert results == []

    def test_custom_shorter_pending_since(self):
        """If given a shorter ``pending_since`` time it should return
        resources that have more recent pending checks."""
        test_resource = factories.Resource()['id']
        one_hour_ago = datetime.datetime.utcnow() - datetime.timedelta(
            hours=1)
        link_checker_results.save_link_checker_result(test_resource, None,
                                                      one_hour_ago)

        results = link_checker_results.get_resources_to_check(
            10, pending_since=datetime.timedelta(hours=0.5))

        assert len(results) == 1
        assert results[0] == test_resource

    def test_custom_longer_pending_since(self):
        """If given a longer ``pending_since`` time it should not return
        resources that have more recent pending checks."""
        test_resource = factories.Resource()['id']
        three_hours_ago = datetime.datetime.utcnow() - datetime.timedelta(
            hours=3)
        link_checker_results.save_link_checker_result(test_resource, None,
                                                      three_hours_ago)

        results = link_checker_results.get_resources_to_check(
            10, pending_since=datetime.timedelta(hours=4))

        assert results == []

    def test_that_old_results_do_not_cause_false_positives(self):
        """

        There was a bug that if a resource had old (older than ``since`` or
        older then ``timeout``) results in the db, that resource's id would be
        returned even if that resource had been checked recently.

        This tests that it doesn't happen anymore.

        """
        resource_1 = factories.Resource()['id']
        resource_2 = factories.Resource()['id']
        resource_3 = factories.Resource()['id']

        thirty_hours_ago = datetime.datetime.utcnow() - datetime.timedelta(
            hours=30)

        link_checker_results.save_link_checker_result(resource_1, True,
                                                      thirty_hours_ago)
        link_checker_results.save_link_checker_result(resource_2, False,
                                                      thirty_hours_ago)
        link_checker_results.save_link_checker_result(resource_3, None,
                                                      thirty_hours_ago)

        link_checker_results.save_link_checker_result(resource_1, None)
        link_checker_results.save_link_checker_result(resource_2, True)
        link_checker_results.save_link_checker_result(resource_3, False)

        resources_to_check = link_checker_results.get_resources_to_check(10)

        assert resources_to_check == []
