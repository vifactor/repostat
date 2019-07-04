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


class GitStats:

    def run(self, args_orig):
        try:
            config = Configuration(args_orig)
            args = config.get_args()
        except ConfigurationException as ce:
            warnings.warn("Configuration exception occured:")
            warnings.warn(ce)
            sys.exit(1)

        # check gnuplot version needed to HTML reports
        if config.is_html_output() and not config.is_valid_gnuplot_version():
            warnings.warn("Invalid gnuplot version. Required "
                          "minimal version: %s. Current version: %s" % (Configuration.GNUPLOT_MINIMAL_VERSION,
                                                                        config.get_gnuplot_version()))
            sys.exit(1)

        output_path = args.output_path
        run_dir = config.get_run_dir()

        print('Output path: %s' % output_path)
        cachefile = os.path.join(output_path, 'gitstats.cache')

        data = GitDataCollector(config.get_args_dict())
        data.load_cache(cachefile)

        # todo: Check loop result. It seems every loop rewrite the collected information in data object.
        #  Is this loop really needed?
        # for git_repo in args.git_repo:
        print('Git path: %s' % args.git_repo)

        prevdir = os.getcwd()
        os.chdir(args.git_repo)

        print('Collecting data...')
        data.collect(args.git_repo)

        os.chdir(prevdir)

        print('Refining data...')
        # data.saveCache(cachefile)
        data.refine()

        os.chdir(run_dir)
        print('Generating report...')
        # fixme: pass GitStatistics object directly when obsolete GitDataCollector is removed
        if config.is_html_output():
            print('Generating HTML report...')
            report = HTMLReportCreator(config, data.repo_statistics)
            report.create(data, output_path)
            self.get_times()
            if sys.stdin.isatty():
                print('You may now run:')
                print('')
                print('   sensible-browser \'%s\'' % os.path.join(output_path, 'general.html').replace("'", "'\\''"))
                print('')
            self.get_times()
        elif config.is_csv_output():
            print('Generating CSV report...')
            report = CSVReportCreator()
            report.create(data.repo_statistics, output_path, config.get_args_dict(), config.is_append_csv())
            print('CSV report created here: %s' % output_path)
            self.get_times()

    @staticmethod
    def get_times():
        time_end = time.time()
        exectime_internal = time_end - time_start
        exectime_external = get_external_execution_time()
        print('Execution time %.5f secs, %.5f secs (%.2f %%) in external commands)'
              % (exectime_internal, exectime_external, (100.0 * exectime_external) / exectime_internal))


if __name__ == '__main__':
    g = GitStats()
    g.run(sys.argv[1:])
