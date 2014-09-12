"""Model code for a database table that stores the results of link checks.

A link checker result records the ID of the resource whose link was checked, the
result of the check (the ``alive`` column, i.e. whether the link was found to be
working or not) and the time.

There can be more than one result for the same resource, so we can tell how many
times consecutively the resource's URL has been dead when we've checked, for how
long it seems to have been dead, etc.

The ``alive`` column may contain ``NULL`` / ``None``, this represents a
"pending" resource check: we have given the resource's ID to a link checker task
and are expecting to receive a link check result soon, but haven't received it
yet.

To prevent the database table from growing bigger and bigger over time, older
results are automatically deleted as new results come in.

This module contains some simple public functions for saving link checker
results and for getting link checker results. Other modules should use these and
should not access the link checker results database table or ORM objects
directly.

"""
import datetime
import uuid

import sqlalchemy
import sqlalchemy.types as types
import sqlalchemy.orm.exc

import ckan.model
import ckan.model.meta


def create_link_checker_results_table():
    """Create the link_checker_results database table.

    If it doesn't already exist.

    This function should be called at CKAN startup time.

    """
    if not _link_checker_results_table.exists():
        _link_checker_results_table.create()


def save_link_checker_result(resource_id, alive, datetime_=None,
                             timeout=None):
    """Save a new link checker result in the database.

    This function also deletes old link checker results from the database so
    that the table doesn't just keep growing indefinitely.

    :param resource_id: the id of the resource that was checked
    :type resource_id: string

    :param alive: whether the resource's URL was found to be alive or not
    :type alive: bool

    :param datetime_: the datetime at which the check was made (optional,
        defaults to the current time) you shouldn't need to use this parameter,
        it exists for testing purposes
    :type datetime: datetime.datetime

    :param timeout: the time delta beyond which old results will be deleted
        (optional, default: one week)
    :type timeout: datetime.timedelta

    """
    # TODO: Make this timeout configurable in the config file.
    if timeout is None:
        timeout = datetime.timedelta(weeks=1)

    # Delete any results older than the timeout.
    q = ckan.model.Session.query(_LinkCheckerResult)
    q = q.filter(
        _LinkCheckerResult.datetime < datetime.datetime.utcnow() - timeout)
    for result in q:
        ckan.model.Session.delete(result)

    # Now create the new link checker result.
    r = _LinkCheckerResult(resource_id, alive, datetime_=datetime_)
    ckan.model.Session.add(r)
    ckan.model.Session.commit()


def get_link_checker_results(resource_id):
    """Return all the link checker results for the given resource.

    Returns both pending and non-pending results.

    Results are sorted most recent first.

    :param resource_id: the id of the resource whose results should be returned
    :type resource_id: string

    :rtype: list of dicts

    """
    q = ckan.model.Session.query(_LinkCheckerResult)
    q = q.filter_by(resource_id=resource_id)
    q = q.order_by(_LinkCheckerResult.datetime.asc())
    return [result.as_dict() for result in q]


# FIXME: What about resources belonging to private datasets?
def get_resources_to_check(n, since=None, pending_since=None):
    """Return up to ``n`` resources to be checked for dead or alive links.

    This function has side effects! Pending resource check results will be added
    to the database for each of the resources returned. This records that we've
    given these resources to a link checker task and are expecting to receive a
    link check result for them soon.

    Resources that don't have any check results in the database will be returned
    first (sorted with the oldest resources first).

    If there are less than ``n`` resources that have no check results, then we
    start re-checking resources that have previously been checked.  Resources
    that do not have any check results (neither completed nor pending) within
    the ``since`` time delta will be returned, sorted with the
    most-recently-checked resources last.

    Resources that have completed check results from less than ``since`` ago
    will never be returned.

    If there are still less than ``n`` resources, then we start re-checking
    resources that have pending checks that we haven't received the results of
    yet. Resources that do not have a completed check within ``since`` and do
    not have a pending check within ``pending_since`` (but may have a pending
    check within ``since``) will be returned. These will be sorted
    oldest-pending-check first.

    Resources that have a pending check from less than ``pending_since`` ago
    will never be returned.

    If that still makes less than ``n`` resources then less than ``n``
    resources will be returned.

    :param n: the maximum number of resources to return
    :type n: int

    :param since: resources that have a completed check within this time delta
        will not be returned (optional, default: 24 hours)
    :type since: datetime.timedelta

    :param pending_since: resources that have a pending check within this time
        delta will not be returned (optional, default: 2 hours)
    :type pending_since: datetime.timedelta

    :returns: the list of resource IDs to be checked
    :rtype: list of strings

    """
    if since is None:
        since = datetime.timedelta(hours=24)

    if pending_since is None:
        pending_since = datetime.timedelta(hours=2)

    # Get the IDs of all the resources that have no check results,
    # oldest resources first.
    resources_with_link_checks = ckan.model.Session.query(
        _LinkCheckerResult.resource_id)
    q = ckan.model.Session.query(ckan.model.Resource.id)
    q = q.filter(~ckan.model.Resource.id.in_(resources_with_link_checks))
    q = q.order_by(ckan.model.Resource.last_modified.asc())
    resources_to_check = [row[0] for row in q]

    if len(resources_to_check) >= n:
        return _create_pending_resource_checks(resources_to_check[:n])

    # Get the IDs of all the resources that do have resource checks, but not
    # within ``since`` time ago.
    since_time_ago = datetime.datetime.utcnow() - since
    do_have_resource_checks_within_since = ckan.model.Session.query(
        _LinkCheckerResult.resource_id).filter(
            _LinkCheckerResult.datetime > since_time_ago)
    q = ckan.model.Session.query(_LinkCheckerResult.resource_id)
    q = q.order_by(_LinkCheckerResult.datetime.asc())
    q = q.filter(~_LinkCheckerResult.resource_id.in_(
        do_have_resource_checks_within_since))
    resources_to_check.extend([row[0] for row in q])
    for row in q:
        resource_id = row[0]
        if resource_id not in resources_to_check:
            resources_to_check.append(resource_id)

    if len(resources_to_check) >= n:
        return _create_pending_resource_checks(resources_to_check[:n])

    # Get the IDs of all the resources that:
    # - Do have link checker results in the db
    # - Do not have any completed results within ``since``
    # - Do not have any pending results within ``pending_since``
    checked_recently = ckan.model.Session.query(
        _LinkCheckerResult.resource_id)
    checked_recently = checked_recently.filter(
        _LinkCheckerResult.alive.in_([True, False]))
    checked_recently = checked_recently.filter(
            _LinkCheckerResult.datetime > since_time_ago)
    recent_pending_check = ckan.model.Session.query(
        _LinkCheckerResult.resource_id)
    recent_pending_check = recent_pending_check.filter_by(
        alive=None)
    pending_time_ago = datetime.datetime.utcnow() - pending_since
    recent_pending_check = recent_pending_check.filter(
        _LinkCheckerResult.datetime > pending_time_ago)
    q = ckan.model.Session.query(_LinkCheckerResult.resource_id)
    q = q.order_by(_LinkCheckerResult.datetime.asc())
    q = q.filter(~_LinkCheckerResult.resource_id.in_(checked_recently))
    q = q.filter(~_LinkCheckerResult.resource_id.in_(recent_pending_check))
    for row in q:
        resource_id = row[0]
        if resource_id not in resources_to_check:
            resources_to_check.append(resource_id)

    return _create_pending_resource_checks(resources_to_check[:n])


def _create_pending_resource_checks(resource_ids):
    """Create pending resource check results for each of the given resources.

    :param resource_ids: the list of resource IDs to create pending checks for
    :type resource_ids: list of strings

    :returns: the list of resource IDs that it was given, unchanged
    :rtype: list of strings

    """
    for resource_id in resource_ids:
        r = _LinkCheckerResult(resource_id, None)
        ckan.model.Session.add(r)
    ckan.model.Session.commit()
    return resource_ids


def _make_uuid():
    return unicode(uuid.uuid4())


_link_checker_results_table = sqlalchemy.Table(
    'link_checker_results', ckan.model.meta.metadata,
    sqlalchemy.Column('id', types.UnicodeText, primary_key=True,
                      default=_make_uuid),
    sqlalchemy.Column('resource_id', types.UnicodeText, nullable=False),
    sqlalchemy.Column('alive', types.Boolean, nullable=True),
    sqlalchemy.Column('datetime', types.DateTime, nullable=False)
)


class _LinkCheckerResult(object):

    """ORM model class for the link_checker_results database table.

    This is a private class - other modules shouldn't use it.

    """
    def __init__(self, resource_id, alive, datetime_=None):
        if datetime_ is None:
            datetime_ = datetime.datetime.utcnow()
        self.datetime = datetime_
        self.resource_id = resource_id
        self.alive = alive

    def as_dict(self):
        """Return a dictionary representation of this link checker result."""
        return dict(id=self.id, datetime=self.datetime,
                    resource_id=self.resource_id,
                    alive=self.alive)


ckan.model.meta.mapper(_LinkCheckerResult, _link_checker_results_table)
