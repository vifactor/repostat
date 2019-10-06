import unittest
from tools.configuration import Configuration
import argparse
import os
import stat


class TestConfiguration(unittest.TestCase):

    def setUp(self) -> None:
        self.repo_folder, test_subdir = os.path.split(os.path.dirname(os.path.abspath(__file__)))
        self.output_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_outs")
        self.read_only_folder = os.path.join(self.output_folder, 'readonly')
        try:
            os.makedirs(self.output_folder)
        except OSError:
            pass
        try:
            os.makedirs(self.read_only_folder)
        except OSError:
            pass
        try:
            os.chmod(self.read_only_folder, stat.S_IREAD)
        except OSError:
            pass

    def test_json_config_parser(self):
        # test config with full json config file
        cli_params = list([
            '--project_name=UTEST Project',
            '--output_format=csv',
            '--config_file=config-test.json',
            self.repo_folder,
            self.output_folder
        ])
        config = Configuration(cli_params)
        args = config.get_args()
        self.assertEqual(args.git_repo, self.repo_folder,
                         "test_json_config_parser result git_repo is different than expected")
        self.assertEqual(args.output_path, self.output_folder,
                         "test_json_config_parser result output_path is different than expected")
        self.assertEqual(args.project_name, 'UTEST Project',
                         "test_json_config_parser result project_name is different than expected")
        self.assertEqual(args.output_format, 'csv',
                         "test_json_config_parser result output_format is different than expected")
        # Config values from json congfig file
        self.assertEqual(args.authors_top, 5,
                         "test_json_config_parser result authors_top is different than expected")
        self.assertEqual(args.max_domains, 11,
                         "test_json_config_parser result max_domains is different than expected")
        self.assertEqual(args.max_authors, 7,
                         "test_json_config_parser result max_authors is different than expected")

    def test_partial_json_config_parser(self):
        # test config with partially filled json config file
        cli_params = list([
            '--project_name=UTEST Project',
            '--output_format=csv',
            '--config_file=partial-config-test.json',
            self.repo_folder,
            self.output_folder
        ])
        config = Configuration(cli_params)
        args = config.get_args()
        self.assertEqual(args.git_repo, self.repo_folder,
                         "test_json_config_parser result git_repo is different than expected")
        self.assertEqual(args.output_path, self.output_folder,
                         "test_json_config_parser result output_path is different than expected")
        self.assertEqual(args.project_name, 'UTEST Project',
                         "test_json_config_parser result project_name is different than expected")
        self.assertEqual(args.output_format, 'csv',
                         "test_json_config_parser result output_format is different than expected")
        # default
        self.assertEqual(args.authors_top, 5,
                         "test_json_config_parser result authors_top is different than expected")
        # from partial config json
        self.assertEqual(args.max_domains, 9,
                         "test_json_config_parser result max_domains is different than expected")
        # from partial config json
        self.assertEqual(args.max_authors, 1,
                         "test_json_config_parser result max_authors is different than expected")

    def test_json_config_parser_defaults(self):
        # test config without json config file
        cli_params = list([
            '--project_name=UTEST Project',
            '--output_format=csv',
            self.repo_folder,
            self.output_folder
        ])
        config = Configuration(cli_params)
        args = config.get_args()
        self.assertEqual(args.git_repo, self.repo_folder,
                         "test_json_config_parser result git_repo is different than expected")
        self.assertEqual(args.output_path, self.output_folder,
                         "test_json_config_parser result output_path is different than expected")
        self.assertEqual(args.project_name, 'UTEST Project',
                         "test_json_config_parser result project_name is different than expected")
        self.assertEqual(args.output_format, 'csv',
                         "test_json_config_parser result output_format is different than expected")
        # Check default config values without config json
        self.assertEqual(args.authors_top, 5,
                         "test_json_config_parser result authors_top is different than expected")
        self.assertEqual(args.max_domains, 10,
                         "test_json_config_parser result max_domains is different than expected")
        self.assertEqual(args.max_authors, 7,
                         "test_json_config_parser result max_authors is different than expected")
        self.assertFalse(args.append_csv)

    def test_configuration_invalid_config_file(self):
        cli_params = list([
            '--project_name=UTEST Project',
            '--output_format=csv',
            '--config_file=not_exists.json',
            self.repo_folder,
            self.output_folder
        ])
        with self.assertRaises(argparse.ArgumentTypeError) as context:
            configuration = Configuration(cli_params)
        self.assertTrue(isinstance(context.exception, argparse.ArgumentTypeError))

    def test_configuration_argparse_usage(self):
        # FIXME: this mainly tests third-party argparse library
        parser = Configuration.get_gitstat_parser()
        parser.print_usage()
        print()
        parser.print_help()

    def test_configuration_argparse_parse(self):
        cli_params = list([
            '--project_name=UTEST Project',
            '--output_format=csv',
            self.repo_folder,
            self.output_folder
        ])
        args = Configuration(cli_params).get_args()
        print(args.project_name)
        print(args)

    def test_configuration_invalid_output_dir(self):
        cli_params = list([
            '--project_name=UTEST Project',
            '--output_format=csv',
            self.repo_folder,
            self.read_only_folder
        ])
        with self.assertRaises(argparse.ArgumentTypeError) as context:
            configuration = Configuration(cli_params)
        self.assertTrue(isinstance(context.exception, argparse.ArgumentTypeError))

    def test_process_and_validate_params_csv_success(self):
        # append_csv param added
        cli_params = list([
            '--project_name=UTEST Project',
            '--output_format=csv',
            '--append_csv',
            self.repo_folder,
            self.output_folder
        ])

        config = Configuration(cli_params)
        args = config.get_args()

        self.assertEqual(args.git_repo, self.repo_folder,
                         "test_process_and_validate_params_csv_success result git_repo is different than expected")
        self.assertEqual(args.output_path, self.output_folder,
                         "test_process_and_validate_params_csv_success result output_path is different than expected")
        self.assertEqual(args.project_name, 'UTEST Project',
                         "test_process_and_validate_params_csv_success result project_name is different than expected")
        self.assertEqual(args.output_format, 'csv',
                         "test_process_and_validate_params_csv_success result output is different than expected")

        # Check options override init configuration
        self.assertTrue(config.is_csv_output())
        self.assertFalse(config.is_html_output())
        # append_csv param True expected
        self.assertTrue(config.is_append_csv())

    def test_process_and_validate_params_html_success(self):
        expected_project_name = "UTEST HTML Project"
        cli_params = list([
            '--project_name=' + expected_project_name,
            self.repo_folder,
            self.output_folder
        ])

        config = Configuration(cli_params)
        args = config.get_args()

        self.assertEqual(args.git_repo, self.repo_folder,
                         "test_process_and_validate_params_csv_success result git_repo is different than expected")
        self.assertEqual(args.output_path, self.output_folder,
                         "test_process_and_validate_params_csv_success result output_path is different than expected")
        self.assertEqual(args.project_name, expected_project_name,
                         "test_process_and_validate_params_csv_success result project_name is different than expected")
        self.assertTrue(config.is_html_output())
        self.assertFalse(config.is_csv_output())
        self.assertFalse(config.is_append_csv())

    def test_gnuplot_version_success_equal(self):
        expected_project_name = "UTEST HTML Project"
        cli_params = list([
            '--project_name=' + expected_project_name,
            self.repo_folder,
            self.output_folder
        ])

        config = Configuration(cli_params)
        # rewrite fields with test data
        config.gnuplot_version_string = '5.2'
        config.GNUPLOT_MINIMAL_VERSION = '5.2'
        self.assertTrue(config.is_valid_gnuplot_version())

    def test_gnuplot_version_success_higher(self):
        expected_project_name = "UTEST HTML Project"
        cli_params = list([
            '--project_name=' + expected_project_name,
            self.repo_folder,
            self.output_folder
        ])

        config = Configuration(cli_params)
        # rewrite fields with test data
        config.gnuplot_version_string = '5.6'
        config.GNUPLOT_MINIMAL_VERSION = '5.2'
        self.assertTrue(config.is_valid_gnuplot_version())

    def test_gnuplot_version_failed_lower(self):
        expected_project_name = "UTEST HTML Project"
        cli_params = list([
            '--project_name=' + expected_project_name,
            self.repo_folder,
            self.output_folder
        ])

        config = Configuration(cli_params)
        # rewrite fields with test data
        config.gnuplot_version_string = '5.0'
        config.GNUPLOT_MINIMAL_VERSION = '5.2'
        self.assertFalse(config.is_valid_gnuplot_version())

    def test_gnuplot_version_faild_not_exists(self):
        expected_project_name = "UTEST HTML Project"
        cli_params = list([
            '--project_name=' + expected_project_name,
            self.repo_folder,
            self.output_folder
        ])

        config = Configuration(cli_params)
        # rewrite fields with test data
        self.assertFalse(config.is_valid_gnuplot_version('-'))
