import ckanext.deadoralive.config as config
import ckanext.deadoralive.tests.helpers as custom_helpers


class TestConfig(custom_helpers.FunctionalTestBaseClass):

    def test_that_it_reads_settings_from_config_file(self):
        """Test that non-default config settings in the config file work."""
        # These non-default settings are in the test.ini config file.
        assert config.recheck_resources_after == 48
        assert config.resend_pending_resources_after == 12

    # TODO: Test falling back on defaults when there's nothing in the config
    # file.
