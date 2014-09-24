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
    plugins.implements(plugins.IRoutes, inherit=True)

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
        config.broken_resource_min_fails = toolkit.asint(
            config_.get(
                "ckanext.deadoralive.broken_resource_min_fails",
                config.broken_resource_min_fails))
        config.broken_resource_min_hours = toolkit.asint(
            config_.get(
                "ckanext.deadoralive.broken_resource_min_hours",
                config.broken_resource_min_hours))

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
            "ckanext_deadoralive_broken_links_by_organization":
                get.broken_links_by_organization,
            "ckanext_deadoralive_broken_links_by_email":
                get.broken_links_by_email,
        }

    # ITemplateHelpers

    def get_helpers(self):
        return {
            "ckanext_deadoralive_get": helpers.get_results,
        }

    # IRoutes

    def before_map(self, map_):
        map_.connect("/broken_links",
                     controller="ckanext.deadoralive.controllers:BrokenLinksController",
                     action="broken_links_by_organization")
        map_.connect("/broken_links_by_email",
                     controller="ckanext.deadoralive.controllers:BrokenLinksController",
                     action="broken_links_by_email")
        return map_
