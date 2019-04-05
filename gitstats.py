#!/usr/bin/env python3
# Copyright (c) 2007-2014 Heikki Hokkanen <hoxu@users.sf.net> & others (see doc/AUTHOR)
# Copyright (c) 2018-2019 Viktor Kopp <vifactor_at_gmail.com> & others
# GPLv2 / GPLv3
import os
import sys
import warnings
import time

from tools.csvreportcreator import CSVReportCreator
from tools.htmlreportcreator import HTMLReportCreator
from tools import GitDataCollector
from tools import get_external_execution_time
from tools import Configuration, ConfigurationException, UsageException

os.environ['LC_ALL'] = 'C'

time_start = time.time()


def usage(conf: dict):
    print("""
Usage: gitstats [options] <gitpath..> <outputpath>

Options:
-c key=value     Override configuration value

Default config values:
%s

output option values: [html,csv]
Please see the manual page for more details.
""" % conf)


class GitStats:

    def run(self, args_orig):
        args = None
        config = Configuration(None)
        try:
            optlist, args = config.process_and_validate_params(args_orig)
        except ConfigurationException as ce:
            warnings.warn("Configuration exception occured:")
            warnings.warn(ce)
            sys.exit(1)
        except UsageException as ue:
            warnings.warn("Usage exception occured:")
            warnings.warn(ue)
            sys.exit(1)

        outputpath = os.path.abspath(args[-1])
        rundir = os.getcwd()

        print('Output path: %s' % outputpath)
        cachefile = os.path.join(outputpath, 'gitstats.cache')

        data = GitDataCollector(config.get_conf())
        data.load_cache(cachefile)

        for gitpath in args[0:-1]:
            print('Git path: %s' % gitpath)

            prevdir = os.getcwd()
            os.chdir(gitpath)

            print('Collecting data...')
            data.collect(gitpath)

            os.chdir(prevdir)

        print('Refining data...')
        # data.saveCache(cachefile)
        data.refine()

        os.chdir(rundir)
        print('Generating report...')
        # fixme: pass GitStatistics object directly when obsolete GitDataCollector is removed
        if config.is_html_output():
            print('Generating HTML report...')
            report = HTMLReportCreator(config, data.repo_statistics)
            report.create(data, outputpath)
            self.get_times()
            if sys.stdin.isatty():
                print('You may now run:')
                print('')
                print('   sensible-browser \'%s\'' % os.path.join(outputpath, 'general.html').replace("'", "'\\''"))
                print('')
            self.get_times()
        elif config.is_csv_output():
            print('Generating CSV report...')
            report = CSVReportCreator()
            report.create(data.repo_statistics, outputpath, config.get_conf())
            print('CSV report created here: %s' % outputpath)
            self.get_times()

    @staticmethod
    def get_times():
        time_end = time.time()
        exectime_internal = time_end - time_start
        exectime_external = get_external_execution_time()
        print('Execution time %.5f secs, %.5f secs (%.2f %%) in external commands)' \
              % (exectime_internal, exectime_external, (100.0 * exectime_external) / exectime_internal))


if __name__ == '__main__':
    g = GitStats()
    g.run(sys.argv[1:])
