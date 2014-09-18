"""Template helper functions provided by this extension."""

import ckan.plugins.toolkit as toolkit


def get_results(resource_id):
    """Return the latest link check result data for the given resource."""

    results = toolkit.get_action("ckanext_deadoralive_get")(
        data_dict={"resource_id": resource_id})
    return results
