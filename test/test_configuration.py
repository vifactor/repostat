import unittest
from tools.configuration import Configuration
import argparse
import json


class TestConfiguration(unittest.TestCase):

    def test_json_config_parser(self):
        # test config with full json config file
        cli_params = list([
            '--project_name=UTEST Project',
            '--output_format=csv',
            '--config_file=config-test.json',
            'e:\\git\\repostat',
            'e:\\gitriports\\repostat'
        ])
        config = Configuration(cli_params)
        args = config.get_args()
        self.assertEqual(args.git_repo, 'e:\\git\\repostat',
                         "test_json_config_parser result git_repo is different than expected")
        self.assertEqual(args.output_path, 'e:\\gitriports\\repostat',
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
            'e:\\git\\repostat',
            'e:\\gitriports\\repostat'
        ])
        config = Configuration(cli_params)
        args = config.get_args()
        self.assertEqual(args.git_repo, 'e:\\git\\repostat',
                         "test_json_config_parser result git_repo is different than expected")
        self.assertEqual(args.output_path, 'e:\\gitriports\\repostat',
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
            'e:\\git\\repostat',
            'e:\\gitriports\\repostat'
        ])
        config = Configuration(cli_params)
        args = config.get_args()
        self.assertEqual(args.git_repo, 'e:\\git\\repostat',
                         "test_json_config_parser result git_repo is different than expected")
        self.assertEqual(args.output_path, 'e:\\gitriports\\repostat',
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

    def test_configuration_invalid_config_file(self):
        cli_params = list([
            '--project_name=UTEST Project',
            '--output_format=csv',
            '--config_file=not_exists.json',
            'e:\\git\\repostat',
            'x:\\gitriports\\repostat'
        ])
        with self.assertRaises(argparse.ArgumentTypeError) as context:
            configuration = Configuration(cli_params)
        self.assertTrue(isinstance(context.exception, argparse.ArgumentTypeError))

    def test_configuration_argparse_usage(self):
        parser = Configuration.get_gitstat_parser()
        parser.print_usage()
        print()
        parser.print_help()

    def test_configuration_argparse_parse(self):
        cli_params = list([
            '--project_name=UTEST Project',
            '--output_format=csv',
            'e:\\git\\repostat',
            'e:\\gitriports\\repostat'
        ])
        args = Configuration(cli_params).get_args()
        print(args.project_name)
        print(args)

    def test_configuration_invalid_output_dir(self):
        cli_params = list([
            '--project_name=UTEST Project',
            '--output_format=csv',
            'e:\\git\\repostat',
            'x:\\gitriports\\repostat'
        ])
        with self.assertRaises(argparse.ArgumentTypeError) as context:
            configuration = Configuration(cli_params)
        self.assertTrue(isinstance(context.exception, argparse.ArgumentTypeError))

    def test_process_and_validate_params_csv_success(self):
        cli_params = list([
            '--project_name=UTEST Project',
            '--output_format=csv',
            'e:\\git\\repostat',
            'e:\\gitriports\\repostat'
        ])

        config = Configuration(cli_params)
        args = config.get_args()

        self.assertEqual(args.git_repo, 'e:\\git\\repostat',
                         "test_process_and_validate_params_csv_success result git_repo is different than expected")
        self.assertEqual(args.output_path, 'e:\\gitriports\\repostat',
                         "test_process_and_validate_params_csv_success result output_path is different than expected")
        self.assertEqual(args.project_name, 'UTEST Project',
                         "test_process_and_validate_params_csv_success result project_name is different than expected")
        self.assertEqual(args.output_format, 'csv',
                         "test_process_and_validate_params_csv_success result output is different than expected")

        # Check options override init configuration
        self.assertTrue(config.is_csv_output())
        self.assertFalse(config.is_html_output())

    def test_process_and_validate_params_html_success(self):
        expected_project_name = "UTEST HTML Project"
        cli_params = list([
            '--project_name=' + expected_project_name,
            'e:\\git\\repostat',
            'e:\\gitriports\\repostat'
        ])

        config = Configuration(cli_params)
        args = config.get_args()

        self.assertEqual(args.git_repo, 'e:\\git\\repostat',
                         "test_process_and_validate_params_csv_success result git_repo is different than expected")
        self.assertEqual(args.output_path, 'e:\\gitriports\\repostat',
                         "test_process_and_validate_params_csv_success result output_path is different than expected")
        self.assertEqual(args.project_name, expected_project_name,
                         "test_process_and_validate_params_csv_success result project_name is different than expected")
        self.assertTrue(config.is_html_output())
        self.assertFalse(config.is_csv_output())
