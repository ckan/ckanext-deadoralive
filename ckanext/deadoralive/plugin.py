"""The deadoralive plugin."""

import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit

import ckanext.deadoralive.model.results as results
import ckanext.deadoralive.config as config
import ckanext.deadoralive.logic.action.get as get
import ckanext.deadoralive.logic.action.update as update
import ckanext.deadoralive.helpers as helpers
import ckanext.deadoralive.logic.auth.update
import ckanext.deadoralive.logic.auth.get


class DeadOrAlivePlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurable)
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IRoutes, inherit=True)
    plugins.implements(plugins.IAuthFunctions)

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
        config.authorized_users = toolkit.aslist(
            config_.get(
                "ckanext.deadoralive.authorized_users",
                config.authorized_users))

    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_resource('theme/resources', 'deadoralive')

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
        map_.connect("deadoralive_broken_links_by_organization",
                     "/organization/broken_links",
                     controller="ckanext.deadoralive.controllers:BrokenLinksController",
                     action="broken_links_by_organization")
        map_.connect("deadoralive_broken_links_by_email",
                     "/ckan-admin/broken_links",
                     controller="ckanext.deadoralive.controllers:BrokenLinksController",
                     action="broken_links_by_email",
                     ckan_icon="link")

        # Make some of this plugin's custom action functions also available at
        # custom URLs. This is to support deadoralive's non-CKAN specific API.
        map_.connect(
            "/deadoralive/get_resources_to_check",
            controller="ckanext.deadoralive.controllers:BrokenLinksController",
            action="get_resources_to_check")
        map_.connect(
            "/deadoralive/get_url_for_resource_id",
            controller="ckanext.deadoralive.controllers:BrokenLinksController",
            action="get_resource_id_for_url")
        map_.connect(
            "/deadoralive/upsert",
            controller="ckanext.deadoralive.controllers:BrokenLinksController",
            action="upsert")

        return map_

    # IAuthFunctions

    def get_auth_functions(self):
        return {
            "ckanext_deadoralive_upsert":
                ckanext.deadoralive.logic.auth.update.upsert,
            "ckanext_deadoralive_get_resources_to_check":
                ckanext.deadoralive.logic.auth.get.get_resources_to_check,
            "ckanext_deadoralive_get":
                ckanext.deadoralive.logic.auth.get.get,
            "ckanext_deadoralive_broken_links_by_organization":
                ckanext.deadoralive.logic.auth.get.broken_links_by_organization,
            "ckanext_deadoralive_broken_links_by_email":
                ckanext.deadoralive.logic.auth.get.broken_links_by_email,
        }
