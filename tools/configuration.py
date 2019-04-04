import os
import sys
import getopt

from tools import get_pipe_output

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


class ConfigurationException(Exception):
    pass


class UsageException(Exception):
    pass


class Configuration():
    conf: dict = None
    GNUPLOT_VERSION_STRING = None
    # By default, gnuplot is searched from path, but can be overridden with the
    # environment variable "GNUPLOT"
    gnuplot_executable = os.environ.get('GNUPLOT', 'gnuplot')

    def __init__(self, config: dict == None):
        if config == None:
            self.conf = dict(default_conf)
        else:
            self.conf = config

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

    def isHtmlOutput(self) -> bool:
        return self.conf['output'] == 'html'

    def isCsvOutput(self) -> bool:
        return self.conf['output'] == 'csv'

    def _check_pre_reqs(self):
        # Py version check
        if sys.version_info < (3, 5):
            raise ConfigurationException("Python 3.5+ is required for repostat")
        # gnuplot version info
        if not self.get_gnuplot_version():
            raise ConfigurationException("gnuplot not found")

    def process_and_validate_params(self, args_orig):
        self._check_pre_reqs()

        optlist, args = getopt.getopt(args_orig, 'hc:', ["help"])
        result_opt = {}
        for o, v in optlist:
            if o == '-c':
                key, value = v.split('=', 1)
                if key not in self.conf:
                    raise KeyError('no such key "%s" in config' % key)
                result_opt[key] = value
                if isinstance(self.conf[key], int):
                    self.conf[key] = int(value)
                else:
                    self.conf[key] = value
            elif o in ('-h', '--help'):
                raise UsageException()

        if len(args) < 2:
            raise UsageException("Too little args")

        if not self.isCsvOutput() and not self.isHtmlOutput():
            raise UsageException(format('Invalid output parameter: %s' % self.conf['output']))

        outputpath = os.path.abspath(args[-1])
        try:
            os.makedirs(outputpath)
        except OSError:
            pass
        if not os.path.isdir(outputpath):
            ConfigurationException(
                'FATAL:Can\'t create Output path. Output path is not a directory or does not exist: %s' % outputpath)

        self.args = args
        self.optlist = result_opt

        return result_opt, args

    def get_conf(self) -> dict:
        return self.conf

    def get_args(self) -> list:
        return self.args

    def get_optlist(self) -> list:
        return self.optlist
