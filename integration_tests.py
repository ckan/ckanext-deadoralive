"""Integration tests for ckanext-deadoralive and deadoralive.

ckanext-deadoralive and deadoralive both have their own detailed tests, but
these don't test whether the two work together: do they agree on the protocol,
e.g. the URLs to send requests to and the params to send and receive back?

This module just adds an extra layer of a few basic integration tests,
where we actually hook up deadoralive to ckanext-deadoralive and see whether
the two work together.

"""
import datetime

import httpretty
import ckan.new_tests.helpers as helpers
import ckan.new_tests.factories as factories
import ckanext.deadoralive.tests.factories as custom_factories
import ckanext.deadoralive.tests.helpers as custom_helpers
import ckanext.deadoralive.model.results as results
import pylons.config as config

import deadoralive


class TestIntegration(custom_helpers.FunctionalTestBaseClass):

    def _forward_to_test_app(self, method, uri, headers):
        """Receive an httpretty request and forward it to a webtest test app.

        Takes an HTTP request in httpretty's format, forwards it to a webtest
        TestApp for CKAN, receives the webtest result, translates that into an
        httpretty result and returns it.

        This is how we hook up the deadoralive link checker service to
        ckanext-deadoralive: The HTTP requests that deadoralive makes are
        intercepted by httpretty and redirected to this method, which sends them
        to a CKAN test app with the deadoralive plugin enabled and then sends
        the response back to httpretty which forwards it back to deadoralive.

        The deadoralive API client code has no idea: it thinks it just made an
        API request to a site and get the response back. The CKAN deadoralive
        plugin code also has no idea: it thinks it just received an HTTP request
        and sent back a response.

        """
        # httpretty puts things like ints and unicode in the headers,
        # but webtest crashes they aren't all strings.
        headers = headers.copy()
        for key in headers:
            headers[key] = str(headers[key])

        # For some reason httpretty puts some of the headers (including the
        # Authorization header) in method.headers instead of in headers.
        # Copy them all to the headers we're going to forward to the test app.
        for key in method.headers:
            if key not in headers:
                headers[key] = str(method.headers[key])

        if method.command == 'POST':
            response = self.app.post(method.path, headers=headers,
                                     params=method.body)
        elif method.command == 'GET':
            response = self.app.get(method.path, headers=headers)

        # requests (or was it httpretty?) seems to require a "server" header
        # but the webtest response doesn't have one.
        if "server" not in response.headers:
            response.headers["server"] = headers["server"]

        # Return an httpretty response tuple based on the webtest response
        # object.
        return (response.status_int, response.headers, response.body)

    @httpretty.activate
    def test(self):
        """Test that deadoralive and ckanext-deadoralive work together.

        Add some resources with working and some with broken links to CKAN,
        run deadoralive, check that it added the right results.

        """
        results.create_database_table()

        user = factories.User()

        # FunctionalTestBaseClass has already made self.app for us, but we
        # need one with our authorized_users config setting in it so replace it
        # with our own.
        config["ckanext.deadoralive.authorized_users"] = user["name"]
        self.app = custom_helpers._get_test_app()

        # The URL of the CKAN site we'll be using.
        # We'll be mocking the URLs on this domain that we expect to be sending
        # requests to.
        ckan_url = "http://test.ckan.org"

        # Mock some working and some broken resource URLs.
        # We'll create resources with these URLs in CKAN below.
        url_1 = "http://demo.ckan.org/url_1"
        httpretty.register_uri(httpretty.GET, url_1, status=200),
        url_2 = "http://demo.ckan.org/url_2"
        httpretty.register_uri(httpretty.GET, url_2, status=500),
        url_3 = "http://demo.ckan.org/url_3"
        httpretty.register_uri(httpretty.GET, url_3, status=200),

        # We're also going to mock the CKAN API URLs that deadoralive will be
        # requesting. We'll catch these requests and then forward them to a CKAN
        # test app.
        # FIXME: It would be nice if we could just mock http://test.ckan.org/*
        # and forward all requests on to the test app, but I don't think
        # httpretty supports this.
        get_resource_ids_url = (
            ckan_url + "/deadoralive/get_resources_to_check")
        httpretty.register_uri(httpretty.GET, get_resource_ids_url,
                               body=self._forward_to_test_app)
        httpretty.register_uri(httpretty.POST, get_resource_ids_url,
                               body=self._forward_to_test_app)

        get_url_for_id_url = ckan_url + "/deadoralive/get_url_for_resource_id"
        httpretty.register_uri(httpretty.GET, get_url_for_id_url,
                               body=self._forward_to_test_app)
        httpretty.register_uri(httpretty.POST, get_url_for_id_url,
                               body=self._forward_to_test_app)

        upsert_result_url = ckan_url + "/deadoralive/upsert"
        httpretty.register_uri(httpretty.GET, upsert_result_url,
                               body=self._forward_to_test_app)
        httpretty.register_uri(httpretty.POST, upsert_result_url,
                               body=self._forward_to_test_app)

        # Create the resources in CKAN whose links will be checked.
        resource_1 = custom_factories.Resource(url=url_1)
        resource_2 = custom_factories.Resource(url=url_2)
        resource_3 = custom_factories.Resource(url=url_3)

        # Call deadoralive: It should get the IDs of the three resources from
        # CKAN.  get each resource's URL from CKAN, test each URL, and then post
        # the test results back to CKAN.
        before = datetime.datetime.utcnow()
        deadoralive.main("--url {0} --apikey {1}".format(
            ckan_url, user["apikey"]).split())
        after = datetime.datetime.utcnow()

        # Now check that the links were checked and the correct results were
        # saved in ckanext-deadoralive's database table.

        # First check the two resources with working links.
        for resource in (resource_1, resource_3):
            result = helpers.call_action("ckanext_deadoralive_get",
                                         resource_id=resource["id"])
            assert result["resource_id"] == resource["id"]
            assert result["alive"] is True
            last_checked = datetime.datetime.strptime(result["last_checked"],
                                                      "%Y-%m-%dT%H:%M:%S.%f")
            assert last_checked > before
            assert last_checked < after
            last_successful = datetime.datetime.strptime(
                result["last_successful"], "%Y-%m-%dT%H:%M:%S.%f")
            assert last_successful > before
            assert last_successful < after
            assert result["num_fails"] == 0
            assert result["pending"] is False
            assert result["pending_since"] is None
            assert result["status"] == 200
            assert result["reason"] == "OK"

        # Now check the expected result for the resource with a broken link.
        result = helpers.call_action("ckanext_deadoralive_get",
                                     resource_id=resource_2["id"])
        assert result["resource_id"] == resource_2["id"]
        assert result["alive"] is False
        last_checked = datetime.datetime.strptime(result["last_checked"],
                                                  "%Y-%m-%dT%H:%M:%S.%f")
        assert last_checked > before
        assert last_checked < after
        assert result["last_successful"] is None
        assert result["num_fails"] == 1
        assert result["pending"] is False
        assert result["pending_since"] is None
        assert result["status"] == 500
        assert result["reason"] == "Internal Server Error"
