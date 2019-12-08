#!/usr/bin/env python3
# Copyright (c) 2007-2014 Heikki Hokkanen <hoxu@users.sf.net> & others (see doc/AUTHOR)
# Copyright (c) 2018-2019 Viktor Kopp <vifactor_at_gmail.com> & others
# GPLv2 / GPLv3
import os
import sys
import warnings
import time
import webbrowser
from distutils import version

from report.htmlreportcreator import HTMLReportCreator
from analysis import GitStatistics
from tools.shellhelper import get_external_execution_time
from tools.configuration import Configuration

os.environ['LC_ALL'] = 'C'

time_start = time.time()


class Requirements:
    gnuplot_minimal_version = version.LooseVersion('5.2')
    python_minimal_version = version.LooseVersion('3.5')
    gnuplot_executable = os.environ.get('GNUPLOT', 'gnuplot')

    def __init__(self, config: Configuration):
        self.gnuplot_version = version.LooseVersion(config.get_gnuplot_version())
        self.python_version = version.LooseVersion(sys.version.split()[0])

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
        Requirements(config).check()
    except EnvironmentError as ee:
        warnings.warn("Environment exception occurred: {}".format(ee))
        sys.exit(1)

    print('Git path: %s' % config.git_repository_path)
    print('Collecting data...', config.do_calculate_contribution())
    repository_statistics = GitStatistics(config.git_repository_path, config.do_calculate_contribution())

    output_path = config.statistics_output_path
    print('Output path: %s' % output_path)
    os.makedirs(output_path, exist_ok=True)

    print('Generating HTML report...')
    HTMLReportCreator(config, repository_statistics).create(output_path)
    print_exec_times()

    url = os.path.join(output_path, 'general.html').replace("'", "'\\''")
    if config.do_open_in_browser():
        webbrowser.open(url, new=2)
    else:
        print("You may open your report in a browser. Path: {}".format(url))


if __name__ == '__main__':
    main()
