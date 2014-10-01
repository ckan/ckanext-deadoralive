import json

import ckan.plugins.toolkit as toolkit


class BrokenLinksController(toolkit.BaseController):

    def broken_links_by_organization(self):

        report = toolkit.get_action(
            "ckanext_deadoralive_broken_links_by_organization")(data_dict={})
        extra_vars = {"organizations": report}

        return toolkit.render("broken_links_by_organization.html",
                              extra_vars=extra_vars)

    def broken_links_by_email(self):

        try:
            report = toolkit.get_action(
                "ckanext_deadoralive_broken_links_by_email")(data_dict={})
        except toolkit.NotAuthorized:
            toolkit.abort(401)
        extra_vars = {"report": report}

        return toolkit.render("broken_links_by_email.html",
                              extra_vars=extra_vars)

    def _call_action(self, action, data_dict=None, key=None):
        context = dict(user=toolkit.c.user)
        if data_dict is None:
            data_dict = dict(toolkit.request.params)
        action_function = toolkit.get_action(action)
        result = action_function(context, data_dict)
        toolkit.response.headers['Content-Type'] = 'application/json'
        if key:
            result = result[key]
        return json.dumps(result)

    def get_resources_to_check(self):
        return self._call_action("ckanext_deadoralive_get_resources_to_check")

    def upsert(self):

        # For some reason True and False are getting turned into "True" and
        # "False". Turn them back.
        data_dict = dict(toolkit.request.params)
        if data_dict.get("alive") == "True":
            data_dict["alive"] = True
        elif data_dict.get("alive") == "False":
            data_dict["alive"] = False

        return self._call_action("ckanext_deadoralive_upsert", data_dict)

    def get_resource_id_for_url(self):

        # Instead of our own get_url_for_resource_id function we just call
        # CKAN's resource_show.

        # deadoralive's get_url_for_resource_id uses resource_id, but CKAN's
        # resource_show uses id. Translate.
        data_dict = dict(toolkit.request.params)
        data_dict["id"] = data_dict["resource_id"]
        del data_dict["resource_id"]

        return self._call_action("resource_show", data_dict, key="url")
