"""The deadoralive plugin."""

import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit

import ckanext.deadoralive.model.results as results
import ckanext.deadoralive.config as config
import ckanext.deadoralive.logic.action.get as get


# Action functions provided by this plugin.

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

    results.upsert(resource_id, alive)


class DeadOrAlivePlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IConfigurable)

    # IConfigurable

    def configure(self, config_):
        results.create_database_table()

        # Update the class variables for the config settings with the values
        # from the config file, *if* they're in the config file.
        config.recheck_resources_after = toolkit.asint(config_.get(
            "ckanext.deadoralive.recheck_resources_after",
            config.recheck_resources_after))
        config.resend_pending_resources_after = toolkit.asint(
            config_.get(
                "ckanext.deadoralive.resend_pending_resources_after",
                config.resend_pending_resources_after))

    # IActions

    def get_actions(self):
        return {
            "ckanext_deadoralive_get_resources_to_check":
                get.get_resources_to_check,
            "ckanext_deadoralive_upsert": upsert,
            "ckanext_deadoralive_get": get.get,
        }
