import os
import unittest
import datetime
import re

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


def get_tags_info():
    tags = {}
    lines = get_pipe_output(['git show-ref --tags']).split('\n')
    for line in lines:
        if len(line) == 0:
            continue
        (hash, tag) = line.split(' ')

        tag = tag.replace('refs/tags/', '')
        output = get_pipe_output(['git log "%s" --pretty=format:"%%at %%aN" -n 1' % hash])
        if len(output) > 0:
            parts = output.split(' ')
            try:
                stamp = int(parts[0])
            except ValueError:
                stamp = 0
            tags[tag] = {'stamp': long(stamp), 'hash': hash,
                              'date': datetime.datetime.fromtimestamp(stamp).strftime('%Y-%m-%d'), 'commits': 0,
                              'authors': {}}

    # collect info on tags, starting from latest
    tags_sorted_by_date_desc = map(lambda el: el[1],
                                   reversed(sorted(map(lambda el: (el[1]['date'], el[0]), tags.items()))))
    prev = None
    for tag in reversed(tags_sorted_by_date_desc):
        cmd = 'git shortlog -s "%s"' % tag
        if prev is not None:
            cmd += ' "^%s"' % prev
        output = get_pipe_output([cmd])
        if len(output) == 0:
            continue
        prev = tag
        for line in output.split('\n'):
            parts = re.split('\s+', line, 2)
            commits = int(parts[1])
            author = parts[2]
            tags[tag]['commits'] += commits
            tags[tag]['authors'][author] = commits
    return tags


class TestPygitMethods(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        this_file_dir = os.path.dirname(os.path.abspath(__file__))
        cls.gs = GitStatistics(this_file_dir)

    def test_authors_count(self):
        gitstats_retrieval_result = int(get_pipe_output(['git shortlog -s %s' % getlogrange(), 'wc -l']))
        self.assertEqual(gitstats_retrieval_result, len(self.gs.authors))

    def test_tags_info(self):
        expected_tags_dict = get_tags_info()
        actual_tags_dict = self.gs.tags

        self.assertListEqual(expected_tags_dict.keys(), actual_tags_dict.keys(),
                             "Tags list is not same estimated by different methods")
        for tagname in expected_tags_dict.keys():
            expected_authors = expected_tags_dict[tagname]['authors']
            actual_authors = actual_tags_dict[tagname]['authors']
            # direct comparison of the two dicts is problematic
            # due to difference in unicode strings parsing via command line and pygit2
            self.assertEquals(len(expected_authors), len(actual_authors))
            self.assertEquals(expected_tags_dict[tagname]['commits'], actual_tags_dict[tagname]['commits'])


if __name__ == '__main__':
    unittest.main()
