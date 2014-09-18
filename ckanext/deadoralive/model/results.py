"""Model code for a database table that stores the results of link checks.

The database table stores one row for each CKAN resource ID containing the
resource ID, the result and time of the resource's last link check, and some
other info.

This module contains some simple public functions for saving and getting
results. Other modules should use these and should not access the results
database table or ORM objects directly.

"""
import datetime

import sqlalchemy
import sqlalchemy.types as types
import sqlalchemy.orm.exc

import ckan.model
import ckan.model.meta


def create_database_table():
    """Create the link_checker_results database table.

    If it doesn't already exist.

    This function should be called at CKAN startup time.

    """
    if not _link_checker_results_table.exists():
        _link_checker_results_table.create()


def upsert(resource_id, alive, status=None, reason=None, last_checked=None):
    """Insert a new result or update the existing result for a resource.

    The ``last_checked`` param is for testing and shouldn't need to be used in
    production.

    :param resource_id: the id of the resource that was checked
    :type resource_id: string

    :param alive: whether the resource's URL was found to be alive or not
    :type alive: bool

    :param status: the HTTP status code returned when requesting the URL,
        or None
    :type status: int or None

    :param reason: the reason for the successful or failed link check
        (e.g. "OK". "Not Found" or "Internal Server Error") or None
    :type reason: string or None

    """
    now = _now()
    try:
        result = _get(resource_id)
        result.alive = alive
        assert alive in (True, False)
        if alive is True:
            result.last_successful = now
            result.num_fails = 0
        elif alive is False:
            result.num_fails += 1
        result.pending = False
        result.pending_since = None
        result.status = status
        result.reason = reason
    except NoResultForResourceError:
        result = _LinkCheckerResult(resource_id, alive, status=status,
                                    reason=reason)
        ckan.model.Session.add(result)
    result.last_checked = last_checked or now
    ckan.model.Session.commit()


class NoResultForResourceError(Exception):
    pass


def _get(resource_id):
    q = ckan.model.Session.query(_LinkCheckerResult)
    q = q.filter_by(resource_id=resource_id)
    try:
        result = q.one()
    except sqlalchemy.orm.exc.NoResultFound:
        raise NoResultForResourceError
    return result


def get(resource_id):
    """Return the result for the given resource ID.

    :param resource_id: the id of the resource whose results should be returned
    :type resource_id: string

    :rtype: dict

    :raises NoResultForResourceError: if there's no result for the given
        resource ID

    """
    return _get(resource_id).as_dict()


# FIXME: What about resources belonging to private datasets?
def get_resources_to_check(n, since=None, pending_since=None):
    """Return up to ``n`` resources to be checked for dead or alive links.

    This function has side effects! Pending results will be added to the
    database for each of the resources returned. This records that we've given
    these resources to a link checker and are expecting to receive results for
    them soon. Resources with pending results won't be given out to another link
    checker again for a while.

    Resources that don't have any results in the database will be returned first
    (sorted with the oldest resources first).

    If there are less than ``n`` resources that have no results, then we start
    re-checking resources that have previously been checked.  Resources that
    don't have any results (neither completed nor pending) within the ``since``
    time delta will be returned, sorted with the most-recently-checked resources
    last.

    Resources that have completed results from less than ``since`` ago will
    never be returned.

    If there are still less than ``n`` resources, then we start re-checking
    resources that have pending results that we haven't received yet.  Resources
    that have a pending result from longer than ``pending_since`` ago will be
    returned. These will be sorted oldest-pending-check first.

    Resources that have a pending result from less than ``pending_since`` ago
    will never be returned.

    If that still makes less than ``n`` resources then less than ``n``
    resources will be returned.

    :param n: the maximum number of resources to return
    :type n: int

    :param since: resources that have a completed result within this time delta
        will not be returned (optional, default: 24 hours)
    :type since: datetime.timedelta

    :param pending_since: resources that have a pending result within this time
        delta will not be returned (optional, default: 2 hours)
    :type pending_since: datetime.timedelta

    :returns: the list of resource IDs to be checked
    :rtype: list of strings

    """
    if since is None:
        since = datetime.timedelta(hours=24)

    if pending_since is None:
        pending_since = datetime.timedelta(hours=2)

    # Get the IDs of all the resources that have no results, oldest resources
    # first.
    resources_with_link_checks = ckan.model.Session.query(
        _LinkCheckerResult.resource_id)
    q = ckan.model.Session.query(ckan.model.Resource.id)
    q = q.filter(~ckan.model.Resource.id.in_(resources_with_link_checks))
    q = q.order_by(ckan.model.Resource.last_modified.asc())
    resources_to_check = [row[0] for row in q]

    if len(resources_to_check) >= n:
        return _make_pending(resources_to_check[:n])

    # Get the IDs of all the resources that:
    # - Do have results
    # - Do not have any pending results
    # - The last result is from > ``since`` ago.
    since_time_ago = _now() - since
    q = ckan.model.Session.query(_LinkCheckerResult.resource_id)
    q = q.filter_by(pending=False)
    q = q.filter(_LinkCheckerResult.last_checked < since_time_ago)
    q = q.order_by(_LinkCheckerResult.last_checked.asc())
    resources_to_check.extend([row[0] for row in q])

    if len(resources_to_check) >= n:
        return _make_pending(resources_to_check[:n])

    # Get the IDs of all the resources that have a pending result from >
    # ``pending_since`` ago.
    pending_time_ago = _now() - pending_since
    q = ckan.model.Session.query(_LinkCheckerResult.resource_id)
    q = q.filter_by(pending=True)
    q = q.filter(_LinkCheckerResult.pending_since < pending_time_ago)
    q = q.order_by(_LinkCheckerResult.pending_since.asc())
    resources_to_check.extend([row[0] for row in q])

    return _make_pending(resources_to_check[:n])


def _now():
    return datetime.datetime.utcnow()


def _make_pending(resource_ids, pending_since=None):
    """Make the results for the given resource IDs as pending."""
    now = _now()
    for resource_id in resource_ids:
        try:
            result = _get(resource_id)
        except NoResultForResourceError:
            result = _LinkCheckerResult(resource_id, None, pending=True)
            ckan.model.Session.add(result)
        result.pending = True
        result.pending_since = pending_since or now
    ckan.model.Session.commit()
    return resource_ids


_link_checker_results_table = sqlalchemy.Table(
    'link_checker_results', ckan.model.meta.metadata,
    sqlalchemy.Column('resource_id', types.UnicodeText, primary_key=True),
    sqlalchemy.Column('alive', types.Boolean, nullable=True),
    sqlalchemy.Column('last_checked', types.DateTime, nullable=True),
    sqlalchemy.Column('last_successful', types.DateTime, nullable=True),
    sqlalchemy.Column('num_fails', types.INT, nullable=False),
    sqlalchemy.Column('pending', types.Boolean, nullable=False),
    sqlalchemy.Column('pending_since', types.DateTime, nullable=True),
    sqlalchemy.Column('status', types.Integer, nullable=True),
    sqlalchemy.Column('reason', types.UnicodeText, nullable=True),
)


class _LinkCheckerResult(object):

    """ORM model class for the link_checker_results database table.

    This is a private class - other modules shouldn't use it.

    """
    def __init__(self, resource_id, alive, pending=False, status=None,
                 reason=None):
        self.resource_id = resource_id
        self.alive = alive
        self.status = status
        self.reason = reason
        now = _now()
        assert alive in (True, False, None)
        if alive is True:
            self.last_checked = now
            self.last_successful = now
            self.num_fails = 0
        elif alive is False:
            self.last_checked = now
            self.last_successful = None
            self.num_fails = 1
        elif alive is None:
            self.last_checked = None
            self.last_successful = None
            self.num_fails = 0
        self.pending = pending
        if pending:
            self.pending_since = now
        else:
            self.pending_since = None

    def as_dict(self):
        """Return a dictionary representation of this link checker result."""
        return dict(
            resource_id=self.resource_id,
            alive=self.alive,
            last_checked=self.last_checked,
            last_successful=self.last_successful,
            num_fails=self.num_fails,
            pending=self.pending,
            pending_since=self.pending_since,
            status=self.status,
            reason=self.reason,
        )


ckan.model.meta.mapper(_LinkCheckerResult, _link_checker_results_table)
