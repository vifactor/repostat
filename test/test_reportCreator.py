import unittest
import os
from tools.reportCreator  import ReportCreator
from tools.gitstatistics import GitStatistics

conf = {
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
    'output':'html'
}

class TestReportCreator(unittest.TestCase):
    gs = None

    @classmethod
    def setUp(cls):
        this_file_dir = os.path.dirname(os.path.abspath(__file__))
        cls.gs = GitStatistics(this_file_dir)

if __name__ == '__main__':
    unittest.main()