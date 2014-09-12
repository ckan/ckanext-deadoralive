"""The deadoralive plugin."""
import ckan.plugins as plugins

import ckanext.deadoralive.model.link_checker_results as model


def get_resources_to_check(context, data_dict):

    # TODO: Authorization.
    # TODO: Validation.
    n = data_dict.get("n", 50)
    return model.get_resources_to_check(n)


def save_link_checker_result(context, data_dict):

    # TODO: Authorization.
    # TODO: Validation.
    resource_id = data_dict["resource_id"]
    alive = data_dict["alive"]
    model.save_link_checker_result(resource_id, alive)


class DeadOrAlivePlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IConfigurable)

    def configure(self, config):
        model.create_link_checker_results_table()

    def get_actions(self):
        return {
            "ckanext_deadoralive_get_resources_to_check":
                get_resources_to_check,
            "ckanext_deadoralive_save_link_checker_result":
                save_link_checker_result,
        }
