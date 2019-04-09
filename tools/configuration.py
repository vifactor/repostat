import os
import sys
import argparse
import json

from tools import get_pipe_output

GITSTAT_VERSION = '0.91'


class ReadableDir(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        prospective_dir=values
        if not os.path.isdir(prospective_dir):
            raise argparse.ArgumentTypeError("readable_dir:{0} is not a valid path".format(prospective_dir))
        if os.access(prospective_dir, os.R_OK):
            setattr(namespace,self.dest,prospective_dir)
        else:
            raise argparse.ArgumentTypeError("readable_dir:{0} is not a readable dir".format(prospective_dir))


class ConfigurationException(Exception):
    pass


class UsageException(Exception):
    pass


class Configuration:

    GNUPLOT_VERSION_STRING = None
    # By default, gnuplot is searched from path, but can be overridden with the
    # environment variable "GNUPLOT"
    gnuplot_executable = os.environ.get('GNUPLOT', 'gnuplot')

    @staticmethod
    def get_release_data_info():
        release_data_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../git_hooks/release_data.json')
        with open(release_data_file, "r") as release_file:
            release_data = json.load(release_file)
        return release_data

    @staticmethod
    def get_gitstat_parser() -> argparse.ArgumentParser:
        release_info = Configuration.get_release_data_info()
        parser = argparse.ArgumentParser(prog='repo_stat',
                                         description='Git repository desktop analyzer. '
                                                     'Analyze and generate git statistics '
                                                     'in HTML format, or export into csv files for further analysis.')

        parser.add_argument('--max_domains', default=10, type=int, help="Display statistic about top active domains")
        parser.add_argument('--max_ext_length', default=10, type=int, help="Collect statistic from files has shorter "
                                                                           "extension as max_ext_length")
        parser.add_argument('--max_authors', default=7, type=int, help="Display statistic about top active authors")
        parser.add_argument('--max_authors_of_months', default=6, type=int, help="Display statistic about top "
                                                                                 "active authors in monthly statistic")
        parser.add_argument('--authors_top', default=5, type=int,
                            help="Display statistic about top active authors in total")
        parser.add_argument('--linear_linestats', default=1, type=int, help="????")
        parser.add_argument('--project_name', default="", type=str,
                            help="Display name of the project git repo contain. "
                                 "This param currently used in csv output format.")
        parser.add_argument('--processes', default=8, type=int, help="????")
        parser.add_argument('--start_date', default='', type=str, help="????")
        parser.add_argument('--output_format', default='html', type=str, choices=['html', 'csv'],
                            help="Statistic output format. Valid values: [html, csv]")
        parser.add_argument('--version', action='version', version='%(prog)s ' + release_info['develop_version'])

        parser.add_argument('git_repo', type=str)
        parser.add_argument('output_path', type=str, action=ReadableDir)
        return parser

    def __init__(self, args_orig=None):
        self.conf = None
        self.args = self._process_and_validate_params(args_orig)

    def get_gnuplot_version(self):
        if self.GNUPLOT_VERSION_STRING is None:
            self.GNUPLOT_VERSION_STRING = get_pipe_output(['%s --version' % self.gnuplot_executable]).split('\n')[0]
        return self.GNUPLOT_VERSION_STRING

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

    @staticmethod
    def get_run_dir():
        return os.getcwd()
