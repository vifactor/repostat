import os
import argparse
import json
import re
import warnings

from tools.shellhelper import get_pipe_output

here = os.path.dirname(os.path.abspath(__file__))


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
            if not os.access(prospective_dir, os.W_OK):
                raise argparse.ArgumentTypeError("Directory {0} is not writable.".format(prospective_dir))
            warnings.warn("Directory {0} already exists. Its content will be rewritten.".format(prospective_dir))
        else:
            is_subdir_of_writable_parent = False
            parent_dir, sub_dir = os.path.split(prospective_dir)
            while sub_dir:
                if os.path.isdir(parent_dir) and os.access(parent_dir, os.W_OK):
                    is_subdir_of_writable_parent = True
                    break
                parent_dir, sub_dir = os.path.split(parent_dir)
            if not is_subdir_of_writable_parent:
                raise argparse.ArgumentTypeError("{0} is not writable directory.".format(parent_dir))

        setattr(namespace, self.dest, prospective_dir)


class ReadableFile(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        file_name = os.path.abspath(os.path.expanduser(values))
        if not os.path.exists(file_name):
            raise argparse.ArgumentTypeError("file:{0} does not exists".format(file_name))
        if not os.path.isfile(file_name):
            raise argparse.ArgumentTypeError("{0} is not a file".format(file_name))
        if not os.access(file_name, os.R_OK):
            raise argparse.ArgumentTypeError("file:{0} is not a readable".format(file_name))

        setattr(namespace, self.dest, file_name)


class Configuration(dict):
    gnuplot_version_string = None
    # By default, gnuplot is searched from path, but can be overridden with the
    # environment variable "GNUPLOT"
    gnuplot_executable = os.environ.get('GNUPLOT', 'gnuplot')
    release_data_dict = None

    @classmethod
    def get_release_data_info(cls):
        if not cls.release_data_dict:
            cls.release_data_dict = cls._read_release_data()
        return cls.release_data_dict

    @classmethod
    def _read_release_data(cls):
        release_data_file_path = os.path.join(here, 'release_data.json')
        with open(release_data_file_path) as release_json_file:
            return json.load(release_json_file)

    @classmethod
    def _read_config_data(cls, path):
        with open(path) as f:
            return json.load(f)

    def __init__(self, args_orig, **kwargs):
        dict.__init__(kwargs)

        self.args = self._parse_sys_argv(args_orig)
        self.git_repository_path = self.args.git_repo
        self.statistics_output_path = self.args.output_path

        self._set_default_configuration()
        if self.args.config_file:
            try:
                read_config = self._read_config_data(self.args.config_file)
                print("Read config", read_config)
                self.update(read_config)
            except Exception as e:
                print("Exception caught: ", e)

    def _set_default_configuration(self):
        self.update({
            "max_domains": 10,
            "max_ext_length": 10,
            "max_authors": 10,
            "max_authors_of_months": 6,
            "authors_top": 5
        })

    def do_open_in_browser(self):
        return not self.args.no_browser

    def is_report_relocatable(self):
        return self.args.copy_assets

    @classmethod
    def _parse_sys_argv(cls, argv):
        release_info = cls.get_release_data_info()
        parser = argparse.ArgumentParser(prog='repostat',
                                         description='Git repository desktop analyzer. '
                                                     'Analyze and generate git statistics '
                                                     'in HTML format')

        parser.add_argument('-v', '--version', action='version', version='%(prog)s ' + release_info['develop_version'])
        parser.add_argument('-c', '--config-file', action=ReadableFile, help="Configuration file path")
        parser.add_argument('--no-browser', action="store_true", help="Do not open report in browser")
        parser.add_argument('--copy-assets', action="store_true",
                            help="Copy assets (images, css, etc.) into report folder (report becomes relocatable)")

        parser.add_argument('git_repo', type=str, action=ReadableDir, help="Path to git repository")
        parser.add_argument('output_path', type=str, action=WritableDir, help="Path to an output directory")

        return parser.parse_args(argv)

    def get_gnuplot_version(self):
        if self.gnuplot_version_string is None:
            reg = re.compile(r"(\d+)\.(\d+)\.?(\d+)?")
            version_str = get_pipe_output(['%s --version' % self.gnuplot_executable]).split('\n')[0]
            match = reg.search(version_str)
            if match:
                self.gnuplot_version_string = version_str[match.span()[0]:match.span()[1]]
        return self.gnuplot_version_string

    @staticmethod
    def get_jinja_version():
        import jinja2 as j2
        return '{} v.{}'.format(j2.__name__, j2.__version__)
