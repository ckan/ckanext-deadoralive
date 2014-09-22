import ckanext.deadoralive.model.results as results


def upsert(context, data_dict, last_checked=None):
    """Save a link check result for a resource.

    :param resource_id: the id of the resource that was checked
    :type resource_id: string

    :param alive: whether or not the link was found to be alive
    :type alive: bool

    :param status: the HTTP status code when the resource was checked,
        e.g. 200, 404 or 500
    :type status: int

    :param reason: the reason for the failed or successful resource check,
        e.g. "OK", "Not Found", "Internal Server Error"
    :type reason: string

    """
    # TODO: Authorization.
    # TODO: Validation.
    resource_id = data_dict["resource_id"]
    alive = data_dict["alive"]
    status = data_dict.get("status")
    reason = data_dict.get("reason")

    results.upsert(resource_id, alive, status=status, reason=reason,
                   last_checked=last_checked)
