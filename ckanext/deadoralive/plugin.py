"""The deadoralive plugin."""

import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit

import ckanext.deadoralive.model.results as results
import ckanext.deadoralive.config as config
import ckanext.deadoralive.logic.action.get as get
import ckanext.deadoralive.logic.action.update as update
import ckanext.deadoralive.helpers as helpers


class DeadOrAlivePlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurable)
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.ITemplateHelpers)

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

    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')

    # IActions

    def get_actions(self):
        return {
            "ckanext_deadoralive_get_resources_to_check":
                get.get_resources_to_check,
            "ckanext_deadoralive_upsert": update.upsert,
            "ckanext_deadoralive_get": get.get,
        }

    # ITemplateHelpers

    def get_helpers(self):
        return {
            "ckanext_deadoralive_get": helpers.get_results,
        }
