import os
import unittest

from tools import GitStatistics
from tools import get_pipe_output

conf = {
    'max_domains': 10,
    'max_ext_length': 10,
    'style': 'gitstats.css',
    'max_authors': 20,
    'authors_top': 5,
    'commit_begin': '',
    'commit_end': 'HEAD',
    'linear_linestats': 1,
    'project_name': '',
    'processes': 8,
    'start_date': ''
}

def getlogrange(defaultrange = 'HEAD', end_only = True):
    commit_range = getcommitrange(defaultrange, end_only)
    if len(conf['start_date']) > 0:
        return '--since="%s" "%s"' % (conf['start_date'], commit_range)
    return commit_range

def getcommitrange(defaultrange = 'HEAD', end_only = False):
    if len(conf['commit_end']) > 0:
        if end_only or len(conf['commit_begin']) == 0:
            return conf['commit_end']
        return '%s..%s' % (conf['commit_begin'], conf['commit_end'])
    return defaultrange

class TestPygitMethods(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        this_file_dir = os.path.dirname(os.path.abspath(__file__))
        cls.gs = GitStatistics(this_file_dir)

    def test_authors_count(self):
        gitstats_retrieval_result = int(get_pipe_output(['git shortlog -s %s' % getlogrange(), 'wc -l']))
        self.assertEqual(gitstats_retrieval_result, len(self.gs.authors))

if __name__ == '__main__':
    unittest.main()