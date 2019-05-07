import os
import sys
import argparse
import json
import re
import warnings
from distutils.version import StrictVersion

from tools import get_pipe_output


class ReadableDir(argparse.Action):

    def __call__(self, parser, namespace, values, option_string=None):
        prospective_dir = os.path.abspath(os.path.expanduser(values))
        if not os.path.isdir(prospective_dir):
            raise argparse.ArgumentTypeError("Path {0} is not valid.".format(prospective_dir))
        if os.access(prospective_dir, os.R_OK):
            setattr(namespace, self.dest, prospective_dir)
        else:
            raise argparse.ArgumentTypeError("Directory {0} is not readable.".format(prospective_dir))


class WritableDir(argparse.Action):

    def __call__(self, parser, namespace, values, option_string=None):
        prospective_dir = os.path.abspath(os.path.expanduser(values))
        if os.path.isdir(prospective_dir):
            warnings.warn("Directory {0} already exists. Its content will be rewritten.".format(prospective_dir))
            if not os.access(prospective_dir, os.W_OK):
                raise argparse.ArgumentTypeError("Directory {0} is not writable.".format(prospective_dir))
        else:
            is_subdir_of_writable_parent = False
            parent_dir, sub_dir = os.path.split(prospective_dir)
            while sub_dir:
                parent_dir, sub_dir = os.path.split(parent_dir)
                if os.path.isdir(parent_dir) and os.access(parent_dir, os.W_OK):
                    is_subdir_of_writable_parent = True
                    break
            if not is_subdir_of_writable_parent:
                raise argparse.ArgumentTypeError("{0} is not writable directory.".format(parent_dir))

        setattr(namespace, self.dest, prospective_dir)


DEFAULT_CONFIG = {
    "max_domains": 10,
    "max_ext_length": 10,
    "max_authors": 7,
    "max_authors_of_months": 6,
    "authors_top": 5
}


class LoadConfigJsonFile(argparse.Action):

    @staticmethod
    def setup_config(namespace, config):
        for key, value in config.items():
            setattr(namespace, key, value)

    @staticmethod
    def load_config_from_file(namespace, file_name):
        config = dict(DEFAULT_CONFIG)
        # try to read json object
        try:
            with open(file_name, "r") as json_file:
                input_conf = json.load(json_file)
                config.update(input_conf)
                LoadConfigJsonFile.setup_config(namespace, config)
        except Exception as ex:
            raise argparse.ArgumentTypeError(
                "file:{0} is not a valid json file. Read error: {1}".format(file_name, ex))

    def __call__(self, parser, namespace, values, option_string=None):
        file_name = values
        if not os.path.exists(file_name):
            raise argparse.ArgumentTypeError("file:{0} is not exists".format(file_name))
        if os.access(file_name, os.R_OK):
            self.load_config_from_file(namespace, file_name)
            setattr(namespace, self.dest, file_name)
        else:
            raise argparse.ArgumentTypeError("file:{0} is not a readable file".format(file_name))


class ConfigurationException(Exception):
    pass


class UsageException(Exception):
    pass


class Configuration:

    GNUPLOT_VERSION_STRING = None
    GNUPLOT_MINIMAL_VERSION = '5.2'
    # By default, gnuplot is searched from path, but can be overridden with the
    # environment variable "GNUPLOT"
    gnuplot_executable = os.environ.get('GNUPLOT', 'gnuplot')
    release_data_dict = None
    repostat_root_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')

    @classmethod
    def get_release_data_info(cls):
        if not cls.release_data_dict:
            cls.release_data_dict = cls._read_release_data()
        return cls.release_data_dict

    @classmethod
    def _read_release_data(cls):
        RELEASE_DATA_FILE = os.path.join(cls.repostat_root_dir, 'git_hooks', 'release_data.json')
        with open(RELEASE_DATA_FILE) as release_json_file:
            release_data = json.load(release_json_file)
            return release_data

    @staticmethod
    def get_gitstat_parser() -> argparse.ArgumentParser:
        release_info = Configuration.get_release_data_info()
        parser = argparse.ArgumentParser(prog='repo_stat',
                                         description='Git repository desktop analyzer. '
                                                     'Analyze and generate git statistics '
                                                     'in HTML format, or export into csv files for further analysis.')

        parser.add_argument('--project_name', default="", type=str,
                            help="Display name of the project git repo contain. "
                                 "This param currently used in csv output format.")
        parser.add_argument('--output_format', default='html', type=str, choices=['html', 'csv'],
                            help="Statistic output format. Valid values: [html, csv]")
        parser.add_argument('--append_csv', action='store_true',
                            help="This option operates in case csv output format. "
                                 "Append exists csv, instead of rewrite.")

        parser.add_argument('--version', action='version', version='%(prog)s ' + release_info['develop_version'])
        parser.add_argument('--config_file', action=LoadConfigJsonFile, default="-")

        parser.add_argument('git_repo', type=str, action=ReadableDir)
        parser.add_argument('output_path', type=str, action=WritableDir)

        return parser

    def __init__(self, args_orig=None):
        self.conf = None
        self.args = self._process_and_validate_params(args_orig)
        if self.args.config_file == "-":
            LoadConfigJsonFile.setup_config(self.args, DEFAULT_CONFIG)

    def query_gnuplot_version(self):
        query_str = get_pipe_output(['%s --version' % self.gnuplot_executable]).split('\n')[0]
        return query_str

    def get_gnuplot_version(self):
        if self.GNUPLOT_VERSION_STRING is None:
            reg = re.compile("(\d+)\.(\d+)\.?(\d+)?")
            version_str = self.query_gnuplot_version()
            match = reg.search(version_str)
            if match:
                self.GNUPLOT_VERSION_STRING = version_str[match.span()[0]:match.span()[1]]
            else:
                self.GNUPLOT_VERSION_STRING = None
        return self.GNUPLOT_VERSION_STRING

    def is_valid_gnuplot_version(self, version: str = None) -> bool:
        current_version = version if version else self.get_gnuplot_version()
        if current_version:
            try:
                return StrictVersion(current_version) >= StrictVersion(self.GNUPLOT_MINIMAL_VERSION)
            except Exception as ex:
                warnings.warn('Gnuplot version number not aplicable. Error: %s \n version number str: %s' % (ex, current_version))
                return False

        else:
            warnings.warn('Gnuplot not installed! Required minimal version: %s' % self.GNUPLOT_MINIMAL_VERSION)
            return False

    def get_gnuplot_executable(self) -> str:
        return self.gnuplot_executable

    @staticmethod
    def get_jinja_version():
        import jinja2 as j2
        return '{} v.{}'.format(j2.__name__, j2.__version__)

    def is_html_output(self) -> bool:
        return self.args.output_format == 'html'

    def is_csv_output(self) -> bool:
        return self.args.output_format == 'csv'

    def _check_pre_reqs(self):
        # Py version check
        if sys.version_info < (3, 5):
            raise ConfigurationException("Python 3.5+ is required for repostat")
        # gnuplot version info
        if not self.get_gnuplot_version():
            raise ConfigurationException("gnuplot not found")

    def _process_and_validate_params(self, args_orig=None):
        self._check_pre_reqs()

        args = self.get_gitstat_parser().parse_args(args_orig)

        try:
            print(args.output_path)
            os.makedirs(args.output_path)
        except OSError:
            pass
        if not os.path.isdir(args.output_path):
            ConfigurationException(
                'FATAL:Can\'t create Output path. Output path is not a directory ' 
                'or does not exist: %s' % args.output_path)

        return args

    def get_args(self):
        return self.args

    def get_args_dict(self):
        return self.args.__dict__

    def is_append_csv(self) -> bool:
        return self.args.append_csv == True

    @staticmethod
    def get_run_dir():
        return os.getcwd()
