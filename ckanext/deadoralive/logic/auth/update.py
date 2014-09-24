import ckanext.deadoralive.config as config


def upsert(context, data_dict):
    """Only the configured user accounts are allowed to upsert link results."""

    return dict(success=context.get("user") in config.authorized_users)
