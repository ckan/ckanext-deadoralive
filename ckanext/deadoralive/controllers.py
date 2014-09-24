import ckan.plugins.toolkit as toolkit


class BrokenLinksController(toolkit.BaseController):

    def broken_links_by_organization(self):

        report = toolkit.get_action(
            "ckanext_deadoralive_broken_links_by_organization")(data_dict={})
        extra_vars = {"organizations": report}

        return toolkit.render("broken_links_by_organization.html",
                              extra_vars=extra_vars)

    def broken_links_by_email(self):

        report = toolkit.get_action(
            "ckanext_deadoralive_broken_links_by_email")(data_dict={})
        extra_vars = {"report": report}

        return toolkit.render("broken_links_by_email.html",
                              extra_vars=extra_vars)
