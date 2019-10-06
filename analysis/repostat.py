#!/usr/bin/env python3
# Copyright (c) 2007-2014 Heikki Hokkanen <hoxu@users.sf.net> & others (see doc/AUTHOR)
# Copyright (c) 2018-2019 Viktor Kopp <vifactor_at_gmail.com> & others
# GPLv2 / GPLv3
import os
import sys
import warnings
import time

from analysis.csvreportcreator import CSVReportCreator
from analysis.htmlreportcreator import HTMLReportCreator
from analysis import GitStatistics
from tools.shellhelper import get_external_execution_time
from tools.configuration import Configuration, ConfigurationException
from distutils import version

os.environ['LC_ALL'] = 'C'

time_start = time.time()


class Requirements:
    gnuplot_minimal_version = version.StrictVersion('5.2')
    python_minimal_version = version.StrictVersion('3.5')
    gnuplot_executable = os.environ.get('GNUPLOT', 'gnuplot')

    def __init__(self, config: Configuration):
        self.gnuplot_version = version.StrictVersion(config.get_gnuplot_version())
        self.python_version = version.StrictVersion(sys.version.split()[0])

    def check(self):
        if self.python_version < self.python_minimal_version:
            raise EnvironmentError("Required Python version {}+".format(self.python_minimal_version))

        if self.gnuplot_version is None:
            EnvironmentError("Html output requires Gnuplot to be installed")

        if self.gnuplot_version < self.gnuplot_minimal_version:
            raise EnvironmentError("Required Gnuplot version {}+".format(self.gnuplot_minimal_version))


def print_exec_times():
    time_end = time.time()
    exectime_internal = time_end - time_start
    exectime_external = get_external_execution_time()
    print('Execution time %.5f secs, %.5f secs (%.2f %%) in external commands)'
          % (exectime_internal, exectime_external, (100.0 * exectime_external) / exectime_internal))


def main():
    try:
        config = Configuration(sys.argv[1:])
        args = config.get_args()
    except ConfigurationException as ce:
        warnings.warn("Configuration exception occurred:")
        warnings.warn(ce)
        sys.exit(1)

    Requirements(config).check()

    print('Git path: %s' % args.git_repo)
    print('Collecting data...')
    repository_statistics = GitStatistics(args.git_repo)

    output_path = args.output_path
    print('Output path: %s' % output_path)

    os.chdir(config.get_run_dir())

    if config.is_html_output():
        print('Generating HTML report...')
        report = HTMLReportCreator(config, repository_statistics)
        report.create(output_path)
        if sys.stdin.isatty():
            print('You may now run:')
            print('')
            print('   sensible-browser \'%s\'' % os.path.join(output_path, 'general.html').replace("'", "'\\''"))
            print('')
    elif config.is_csv_output():
        print('Generating CSV report...')
        report = CSVReportCreator()
        report.create(repository_statistics, output_path, config.get_args_dict(), config.is_append_csv())
        print('CSV report created here: %s' % output_path)
    print_exec_times()


if __name__ == '__main__':
    main()
