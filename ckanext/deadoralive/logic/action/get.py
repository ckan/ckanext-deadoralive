import datetime

import ckanext.deadoralive.model.results as results
import ckanext.deadoralive.config as config


def get_resources_to_check(context, data_dict):
    """Return a list of up to ``n`` resource IDs to be checked.

    Returns up to ``n`` resource IDs to be checked for broken links.

    Resources that have not been checked before will be returned first, oldest
    resources first.

    Resources that have not been checked in the last 24 hours (configurable:
    ``ckanext.deadoralive.recheck_resources_after``) will be returned next,
    most-recently-checked resources last.

    As soon as a resource's ID is returned by this function that resource is
    considered to have a "pending" check (we are expecting to receive a link
    check result for that resource soon). Resources with pending checks will
    not be returned by this function again for at least 2 hours (configurable:
    ``ckanext.deadoralive.resend_pending_resources_after``).

    :param n: the maximum number of resources to return at once
    :type n: int

    :rtype: list of strings

    """
    # TODO: Authorization.
    # TODO: Validation.

    recheck_resources_after = config.recheck_resources_after
    since_delta = datetime.timedelta(hours=recheck_resources_after)
    resend_pending_resources_after = (
        config.resend_pending_resources_after)
    pending_since_delta = datetime.timedelta(
        hours=resend_pending_resources_after)

    n = data_dict.get("n", 50)

    return results.get_resources_to_check(n, since=since_delta,
                                          pending_since=pending_since_delta)


def get(context, data_dict):
    """Get the latest link check result data for a resource.

    :param resource_id: the resource to return the result data for
    :type resource_id: string

    :returns: the latest link check data for the resource, or None if there are
      no results for this resource
    :rtype: dict or None

    """
    # TODO: Authorization.
    # TODO: Validation.
    resource_id = data_dict["resource_id"]

    try:
        result = results.get(resource_id)
    except results.NoResultForResourceError:
        return None

    # datetimes aren't JSON serializable.
    result["last_checked"] = result["last_checked"].isoformat()
    if result["last_successful"]:
        result["last_successful"] = result["last_successful"].isoformat()
    if result["pending_since"]:
        result["pending_since"] = result["pending_since"].isoformat()

    # Add "broken" to the result - whether or not we consider the link to be
    # broken according to our "it must have been dead for at least N consecutive
    # checks over a period of at least M hours" test.
    n = config.broken_resource_min_fails
    m = config.broken_resource_min_hours
    m_hours_ago = datetime.datetime.utcnow() - datetime.timedelta(hours=m)

    # Innocent until proven guilty.
    result["broken"] = False

    if result["last_successful"]:
        last_successful = datetime.datetime.strptime(result["last_successful"],
                                                     "%Y-%m-%dT%H:%M:%S.%f")
    else:
        last_successful = None

    # We won't mark a link as "working" if it has never been checked
    # successfully. It may not pass our test to be marked as broken if it hasn't
    # been checked n times, but we will leave it unmarked rather than mark it
    # as working.
    if not result["last_successful"]:
        result["broken"] = None

    # Mark the resource as broken if it has at least n consecutive fails over
    # a period of at least m hours.
    if result["num_fails"] >= n:
        if last_successful is None or last_successful < m_hours_ago:
            result["broken"] = True

    return result
