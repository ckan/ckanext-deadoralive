import ckan.new_tests.helpers as helpers

import ckanext.deadoralive.tests.helpers as custom_helpers
import ckanext.deadoralive.tests.factories as factories


class TestGetResourcesToCheck(custom_helpers.FunctionalTestBaseClass):
    """Tests for the get_resources_to_check() action function.

    The details of which resources are returned is tested in the model tests,
    here we just test the stuff that the action function itself does.

    """
    def test_get_resources_to_check(self):
        """Simple test: call get_resources_to_check() and test the result."""
        factories.Resource()
        factories.Resource()
        factories.Resource()

        resource_ids = helpers.call_action(
            "ckanext_deadoralive_get_resources_to_check")

        assert len(resource_ids) == 3

    # TODO: Test config setting reading and defaults, test that they get
    #       passed to model.
    # TODO: Test invalid config setting (move config setting parsing into its
    #       own function)
    # TODO: Test n param.
    # TODO: Test validation.


class TestUpsert(custom_helpers.FunctionalTestBaseClass):

    def test_upsert(self):
        """Simple test: call upsert() then call get() and check the result."""
        resource = factories.Resource()

        helpers.call_action("ckanext_deadoralive_upsert",
                            resource_id=resource["id"], alive=True)

        result = helpers.call_action("ckanext_deadoralive_get",
                                     resource_id=resource["id"])

        assert result["resource_id"] == resource["id"]
        assert result["alive"] is True
