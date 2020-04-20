#!/usr/bin/env python3
# Copyright (c) 2007-2014 Heikki Hokkanen <hoxu@users.sf.net> & others
# Copyright (c) 2018-2020 Viktor Kopp <vifactor_at_gmail.com> & others
# GPLv2 / GPLv3
import os
import sys
import warnings
import time
import webbrowser

from report.htmlreportcreator import HTMLReportCreator
from analysis import GitStatistics
from analysis.gitrepository import GitRepository
from tools.shellhelper import get_external_execution_time
from tools.configuration import Configuration

os.environ['LC_ALL'] = 'C'

time_start = time.time()


def print_exec_times():
    time_end = time.time()
    exectime_internal = time_end - time_start
    exectime_external = get_external_execution_time()
    print('Execution time %.5f secs, %.5f secs (%.2f %%) in external commands)'
          % (exectime_internal, exectime_external, (100.0 * exectime_external) / exectime_internal))


def main():
    try:
        config = Configuration(sys.argv[1:])
    except EnvironmentError as ee:
        warnings.warn("Environment exception occurred: {}".format(ee))
        sys.exit(1)

    print('Git path: %s' % config.git_repository_path)
    print('Collecting data...', config.do_calculate_contribution())
    repo_statistics = GitStatistics(config.git_repository_path,
                                          config.do_calculate_contribution(),
                                          config.do_process_tags())
    repository_statistics = GitRepository(config.git_repository_path)

    output_path = config.statistics_output_path
    print('Output path: %s' % output_path)
    os.makedirs(output_path, exist_ok=True)

    print('Generating HTML report...')
    HTMLReportCreator(config, repo_statistics, repository_statistics).create(output_path)
    print_exec_times()

    url = os.path.join(output_path, 'general.html').replace("'", "'\\''")
    if config.do_open_in_browser():
        webbrowser.open(url, new=2)
    else:
        print("You may open your report in a browser. Path: {}".format(url))


if __name__ == '__main__':
    main()
