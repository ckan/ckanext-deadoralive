import ckanext.deadoralive.model.results as results


def upsert(context, data_dict):
    """Save a link check result for a resource.

    :param resource_id: the id of the resource that was checked
    :type resource_id: string

    :param alive: whether or not the link was found to be alive
    :type alive: bool

    """
    # TODO: Authorization.
    # TODO: Validation.
    resource_id = data_dict["resource_id"]
    alive = data_dict["alive"]
    status = data_dict.get("status")
    reason = data_dict.get("reason")

    results.upsert(resource_id, alive, status=status, reason=reason)
