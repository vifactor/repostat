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
from analysis import GitDataCollector
from tools.shellhelper import get_external_execution_time
from tools.configuration import Configuration, ConfigurationException

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
        args = config.get_args()
    except ConfigurationException as ce:
        warnings.warn("Configuration exception occurred:")
        warnings.warn(ce)
        sys.exit(1)

    # check gnuplot version needed to HTML reports
    if config.is_html_output() and not config.is_valid_gnuplot_version():
        warnings.warn("Invalid gnuplot version. Required "
                      "minimal version: %s. Current version: %s" % (Configuration.GNUPLOT_MINIMAL_VERSION,
                                                                    config.get_gnuplot_version()))
        sys.exit(1)

    print('Git path: %s' % args.git_repo)
    print('Collecting data...')
    data = GitDataCollector(config.get_args_dict(), args.git_repo)

    print('Refining data...')
    data.refine()

    output_path = args.output_path
    print('Output path: %s' % output_path)

    os.chdir(config.get_run_dir())

    # fixme: pass GitStatistics object directly when obsolete GitDataCollector is removed
    if config.is_html_output():
        print('Generating HTML report...')
        report = HTMLReportCreator(config, data.repo_statistics)
        report.create(data, output_path)
        if sys.stdin.isatty():
            print('You may now run:')
            print('')
            print('   sensible-browser \'%s\'' % os.path.join(output_path, 'general.html').replace("'", "'\\''"))
            print('')
    elif config.is_csv_output():
        print('Generating CSV report...')
        report = CSVReportCreator()
        report.create(data.repo_statistics, output_path, config.get_args_dict(), config.is_append_csv())
        print('CSV report created here: %s' % output_path)
    print_exec_times()


if __name__ == '__main__':
    main()
