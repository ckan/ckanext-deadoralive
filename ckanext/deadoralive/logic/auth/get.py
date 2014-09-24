"""Authorization functions for the action functions in action/get.py."""
import ckan.plugins.toolkit as toolkit
import ckanext.deadoralive.config as config


def get_resources_to_check(context, data_dict):
    """Only the configured users can get the get_resources_to_check API."""
    return dict(success=context.get("user") in config.authorized_users)


@toolkit.auth_allow_anonymous_access
def get(context, data_dict):
    """Anyone can get the broken link report for a resource."""
    return dict(success=True)


@toolkit.auth_allow_anonymous_access
def broken_links_by_organization(context, data_dict):
    """Anyone can see the broken_links_by_organization report."""
    return dict(success=True)


def broken_links_by_email(context, data_dict):
    """Only sysadmins can see the broken_links_by_email report."""
    return dict(success=False)
