"""Tests for model/results.py."""
import datetime

import nose.tools

import ckan.new_tests.helpers as helpers
import ckan.new_tests.factories as factories

import ckanext.deadoralive.model.results as results


class TestUpsertAndGet(object):
    """Tests for the upsert() and get() functions."""
    def setup(self):
        helpers.reset_db()
        results.create_database_table()

    def test_insert_successful_result(self):
        """Test checking a resource for the first time when the link is working.

        """
        before = datetime.datetime.utcnow()
        results.upsert("test_resource_id", True)
        after = datetime.datetime.utcnow()
        result = results.get("test_resource_id")
        assert result["resource_id"] == "test_resource_id"
        assert result["alive"] is True
        assert result["last_checked"] > before
        assert result["last_checked"] < after
        assert result["last_successful"] > before
        assert result["last_successful"] < after
        assert result["num_fails"] == 0
        assert result["pending"] is False
        assert result["pending_since"] is None

    def test_insert_failed_result(self):
        """Test checking a resource for the first time when the link is broken.

        """
        before = datetime.datetime.utcnow()
        results.upsert("test_resource_id", False)
        after = datetime.datetime.utcnow()
        result = results.get("test_resource_id")
        assert result["resource_id"] == "test_resource_id"
        assert result["alive"] is False
        assert result["last_checked"] > before
        assert result["last_checked"] < after
        assert result["last_successful"] is None
        assert result["num_fails"] == 1
        assert result["pending"] is False
        assert result["pending_since"] is None

    def test_update_with_successful_result(self):
        """Test updating a resource's row with a new successful result."""
        results.upsert("test_resource_id", False)
        before = datetime.datetime.utcnow()

        results.upsert("test_resource_id", True)
        after = datetime.datetime.utcnow()

        result = results.get("test_resource_id")
        assert result["resource_id"] == "test_resource_id"
        assert result["alive"] is True
        assert result["last_checked"] > before
        assert result["last_checked"] < after
        assert result["last_successful"] > before
        assert result["last_successful"] < after
        assert result["num_fails"] == 0
        assert result["pending"] is False
        assert result["pending_since"] is None

    def test_update_with_failed_result(self):
        """Test updating a resource's row with a new failed result."""
        results.upsert("test_resource_id", True)

        before = datetime.datetime.utcnow()
        results.upsert("test_resource_id", False)
        after = datetime.datetime.utcnow()

        result = results.get("test_resource_id")
        assert result["resource_id"] == "test_resource_id"
        assert result["alive"] is False
        assert result["last_checked"] > before
        assert result["last_checked"] < after
        assert result["last_successful"] < before
        assert result["num_fails"] == 1
        assert result["pending"] is False
        assert result["pending_since"] is None

    def test_incrementing_num_fails(self):
        """Test that repeated bad results increment num_fails."""

        results.upsert("test_resource_id", False)
        results.upsert("test_resource_id", False)
        before = datetime.datetime.utcnow()
        results.upsert("test_resource_id", False)
        after = datetime.datetime.utcnow()

        result = results.get("test_resource_id")

        assert result["num_fails"] == 3
        assert result["last_checked"] > before
        assert result["last_checked"] < after

    def test_reset_num_fails(self):
        """Test that a successful result resets num_fails to 0."""

        results.upsert("test_resource_id", False)
        results.upsert("test_resource_id", False)
        before = datetime.datetime.utcnow()
        results.upsert("test_resource_id", True)
        after = datetime.datetime.utcnow()

        result = results.get("test_resource_id")

        assert result["num_fails"] == 0
        assert result["last_checked"] > before
        assert result["last_checked"] < after
        assert result["last_successful"] > before
        assert result["last_successful"] < after

    def test_reset_pending_status(self):
        """Test that either a successful or failed result resets pending and
        pending_since.

        """
        import ckan.model

        result = results._LinkCheckerResult(
            "test_resource_id", None, pending=True)
        result.pending = True
        result.pending_since
        ckan.model.Session.add(result)
        ckan.model.Session.commit()

        results.upsert("test_resource_id", True)

        result = results.get("test_resource_id")

        assert result["pending"] is False
        assert result["pending_since"] is None

    def test_get_result_that_does_not_exist(self):
        """get() should raise NoResultForResourceError if asked for the result
        for a resource ID that has no results."""

        nose.tools.assert_raises(results.NoResultForResourceError,
                                 results.get, "test_resource_id")

    def test_pending_result_does_not_change_num_fails(self):
        """Inserting a new pending result should not change num_fails.

        If we already have a results row for a resource, then we change that row
        to make a pending result, this should not change num_fails or other
        fields.

        """
        # Make a resource with 1 success then 3 consecutive fails.
        results.upsert("test_resource_id", True)
        last_successful = results.get("test_resource_id")["last_successful"]
        results.upsert("test_resource_id", False)
        results.upsert("test_resource_id", False)
        results.upsert("test_resource_id", False)
        num_fails = results.get("test_resource_id")["num_fails"]
        last_checked = results.get("test_resource_id")["last_checked"]

        before = datetime.datetime.utcnow()
        results._make_pending(["test_resource_id"])
        after = datetime.datetime.utcnow()

        result = results.get("test_resource_id")
        assert result["num_fails"] == num_fails
        assert result["last_successful"] == last_successful
        assert result["last_checked"] == last_checked
        assert result["alive"] is False
        assert result["pending"] is True
        assert result["pending_since"] > before
        assert result["pending_since"] < after

    def test_initial_pending_result(self):
        """Test creating a pending result for a resource that has no results.

        """
        before = datetime.datetime.utcnow()
        results._make_pending(["test_resource_id"])
        after = datetime.datetime.utcnow()

        result = results.get("test_resource_id")
        assert result["num_fails"] == 0
        assert result["last_successful"] is None
        assert result["last_checked"] is None
        assert result["alive"] is None
        assert result["pending"] is True
        assert result["pending_since"] > before
        assert result["pending_since"] < after


class TestGetResourcesToCheck(object):
    """Tests for the get_resources_to_check() function."""

    def setup(self):
        helpers.reset_db()
        results.create_database_table()

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

        resources_to_check = results.get_resources_to_check(10)

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

        resources_to_check = results.get_resources_to_check(5)

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
        results.upsert(resource_1, True, twenty_hours_ago)
        results.upsert(resource_2, True, twenty_hours_ago)
        results.upsert(resource_3, True, twenty_hours_ago)
        results.upsert(resource_4, True, twenty_hours_ago)
        results.upsert(resource_5, True, twenty_hours_ago)

        resources_to_check = results.get_resources_to_check(10)

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
        results.upsert(resource_1, True, twenty_hours_ago)
        results.upsert(resource_2, True, twenty_hours_ago)
        results.upsert(resource_3, True, twenty_hours_ago)
        results.upsert(resource_4, True, twenty_hours_ago)
        results.upsert(resource_5, True, twenty_hours_ago)
        resource_6 = factories.Resource()['id']
        resource_7 = factories.Resource()['id']
        resource_8 = factories.Resource()['id']
        resource_9 = factories.Resource()['id']
        resource_10 = factories.Resource()['id']

        resources_to_check = results.get_resources_to_check(10)

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
        results.upsert(resource_1, True, twenty_hours_ago)
        results.upsert(resource_2, True, twenty_hours_ago)
        results.upsert(resource_3, True, twenty_hours_ago)
        results.upsert(resource_4, True, twenty_hours_ago)
        results.upsert(resource_5, True, twenty_hours_ago)
        resource_6 = factories.Resource()['id']
        resource_7 = factories.Resource()['id']
        resource_8 = factories.Resource()['id']
        resource_9 = factories.Resource()['id']
        resource_10 = factories.Resource()['id']
        # We mix up the order in which these resources were checked a bit.
        results.upsert(
            resource_7, True, now - datetime.timedelta(hours=34))
        results.upsert(
            resource_6, True, now - datetime.timedelta(hours=33))
        results.upsert(
            resource_9, True, now - datetime.timedelta(hours=32))
        results.upsert(
            resource_10, True, now - datetime.timedelta(hours=31))
        results.upsert(
            resource_8, True, now - datetime.timedelta(hours=30))

        resources_to_check = results.get_resources_to_check(10)

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
        results.upsert(resource_1, True, twenty_hours_ago)
        results.upsert(resource_2, True, twenty_hours_ago)
        results.upsert(resource_3, True, twenty_hours_ago)
        results.upsert(resource_4, True, twenty_hours_ago)
        results.upsert(resource_5, True, twenty_hours_ago)

        # Create 5 resources with pending checks from < 2 hours ago.
        resource_6 = factories.Resource()['id']
        resource_7 = factories.Resource()['id']
        resource_8 = factories.Resource()['id']
        resource_9 = factories.Resource()['id']
        resource_10 = factories.Resource()['id']
        one_hour_ago = now - datetime.timedelta(hours=1)
        results._make_pending(
            [resource_6, resource_7, resource_8, resource_9, resource_10],
            one_hour_ago)

        # Create 5 resources that were last checked more than 24 hours ago.
        resource_11 = factories.Resource()['id']
        resource_12 = factories.Resource()['id']
        resource_13 = factories.Resource()['id']
        resource_14 = factories.Resource()['id']
        resource_15 = factories.Resource()['id']
        results.upsert(resource_11, True, now - datetime.timedelta(hours=35))
        results.upsert(resource_12, True, now - datetime.timedelta(hours=34))
        results.upsert(resource_13, True, now - datetime.timedelta(hours=33))
        results.upsert(resource_14, True, now - datetime.timedelta(hours=32))
        results.upsert(resource_15, True, now - datetime.timedelta(hours=31))

        resources_to_check = results.get_resources_to_check(10)

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
        results._make_pending(
            [resource_1, resource_2, resource_3, resource_4, resource_5],
            five_hours_ago)

        resources_to_check = results.get_resources_to_check(10)

        assert resources_to_check == [resource_1, resource_2, resource_3,
                                      resource_4, resource_5]

    def test_that_it_creates_pending_checks(self):
        """get_resources_to_check() should create pending link checker results
        for all the resources it returns."""

        # A resource that has never been checked.
        resource_1 = factories.Resource()['id']

        # A resource that was checked > 24 hours ago.
        resource_2 = factories.Resource()['id']
        thirty_hours_ago = datetime.datetime.utcnow() - datetime.timedelta(
            hours=30)
        results.upsert(resource_2, True, thirty_hours_ago)

        # A resource with a pending check from > 2 hours ago.
        resource_3 = factories.Resource()['id']
        three_hours_ago = datetime.datetime.utcnow() - datetime.timedelta(
            hours=3)
        results._make_pending([resource_3], three_hours_ago)

        results.get_resources_to_check(10)

        for resource in (resource_1, resource_2, resource_3):
            result = results.get(resource)
            assert result["pending"] is True

    def test_custom_shorter_since(self):
        """If given a shorter ``since`` time it should return resources that
        have been checked more recently."""
        test_resource = factories.Resource()['id']
        ten_hours_ago = datetime.datetime.utcnow() - datetime.timedelta(
            hours=10)
        results.upsert(test_resource, True, ten_hours_ago)

        results_ = results.get_resources_to_check(
            10, since=datetime.timedelta(hours=5))

        assert len(results_) == 1
        assert results_[0] == test_resource

    def test_custom_longer_since(self):
        """If given a longer ``since`` time it should not return resources that
        were checked more recently."""
        test_resource = factories.Resource()['id']
        thirty_hours_ago = datetime.datetime.utcnow() - datetime.timedelta(
            hours=30)
        results.upsert(test_resource, True, thirty_hours_ago)

        results_ = results.get_resources_to_check(
            10, since=datetime.timedelta(hours=48))

        assert results_ == []

    def test_custom_shorter_pending_since(self):
        """If given a shorter ``pending_since`` time it should return
        resources that have more recent pending checks."""
        test_resource = factories.Resource()['id']
        one_hour_ago = datetime.datetime.utcnow() - datetime.timedelta(
            hours=1)
        results._make_pending([test_resource], one_hour_ago)

        results_ = results.get_resources_to_check(
            10, pending_since=datetime.timedelta(hours=0.5))

        assert len(results_) == 1
        assert results_[0] == test_resource

    def test_custom_longer_pending_since(self):
        """If given a longer ``pending_since`` time it should not return
        resources that have more recent pending checks."""
        test_resource = factories.Resource()['id']
        three_hours_ago = datetime.datetime.utcnow() - datetime.timedelta(
            hours=3)
        results._make_pending([test_resource], three_hours_ago)

        results_ = results.get_resources_to_check(
            10, pending_since=datetime.timedelta(hours=4))

        assert results_ == []
