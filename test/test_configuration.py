import unittest
from tools.configuration import Configuration, ConfigurationException


class TestConfiguration(unittest.TestCase):
    default_conf = {
        'max_domains': 10,
        'max_ext_length': 10,
        'style': 'gitstats.css',
        'max_authors': 7,
        'max_authors_of_months': 6,
        'authors_top': 5,
        'commit_begin': '',
        'commit_end': 'HEAD',
        'linear_linestats': 1,
        'project_name': '',
        'processes': 8,
        'start_date': '',
        'output': 'html'
    }

    test_conf = {
        'max_domains': 123,
        'max_ext_length': 10,
        'style': 'gitstats.css',
        'max_authors': 7,
        'max_authors_of_months': 6,
        'authors_top': 5,
        'commit_begin': '',
        'commit_end': 'HEAD',
        'linear_linestats': 1,
        'project_name': '',
        'processes': 8,
        'start_date': '',
        'output': 'html'
    }

    def test_configuration_init_def_conf(self):
        # default config initialization test
        config = Configuration(None)
        self.assertEqual(config.get_conf(), self.default_conf)

    def test_configuration_init_test_conf(self):
        # test config initialization test
        config = Configuration(self.test_conf)
        self.assertEqual(config.get_conf(), self.test_conf)

    def test_process_and_validate_params_csv_success(self):
        cli_params = list([
            '-cproject_name=UTEST Project',
            '-coutput=csv',
            'e:\\git\\repostat',
            'e:\\gitriports\\repostat'
        ])

        config = Configuration(None)
        opt, args = config.process_and_validate_params(cli_params)

        expected_opt = {
            'project_name': 'UTEST Project',
            'output': 'csv'
        }
        expected_args = ['e:\\git\\repostat', 'e:\\gitriports\\repostat']

        self.assertEqual(expected_opt, opt,
                         "test_process_and_validate_params_csv_success result OPT is different than expected")
        self.assertEqual(expected_args, args,
                         "test_process_and_validate_params_csv_success result ARGS is different than expected")

        # Check options override init configuration
        self.assertEqual(config.get_conf()['project_name'], "UTEST Project")
        self.assertEqual(config.get_conf()['output'], "csv")
        self.assertTrue(config.isCsvOutput())
        self.assertFalse(config.isHtmlOutput())

    def test_process_and_validate_params_html_success(self):
        expected_project_name = "UTEST HTML Project"
        cli_params = list([
            '-cproject_name=' + expected_project_name,
            'e:\\git\\repostat',
            'e:\\gitriports\\repostat'
        ])

        config = Configuration(None)
        opt, args = config.process_and_validate_params(cli_params)

        expected_opt = {
            'project_name': expected_project_name
        }
        expected_args = ['e:\\git\\repostat', 'e:\\gitriports\\repostat']

        self.assertEqual(expected_opt, opt,
                         "test_process_and_validate_params_html_success result OPT is different than expected")
        self.assertEqual(expected_args, args,
                         "test_process_and_validate_params_html_success result ARGS is different than expected")

        # Check options override init configuration
        self.assertEqual(config.get_conf()['project_name'], expected_project_name)
        # html is the default output format
        self.assertEqual(config.get_conf()['output'], "html")
        self.assertTrue(config.isHtmlOutput())
        self.assertFalse(config.isCsvOutput())
