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


def getlogrange(defaultrange='HEAD', end_only=True):
    commit_range = getcommitrange(defaultrange, end_only)
    if len(conf['start_date']) > 0:
        return '--since="%s" "%s"' % (conf['start_date'], commit_range)
    return commit_range


def getcommitrange(defaultrange='HEAD', end_only=False):
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


def get_stat_summary_counts(line):
    numbers = re.findall('\d+', line)
    if len(numbers) == 1:
        # neither insertions nor deletions: may probably only happen for "0 files changed"
        numbers.append(0)
        numbers.append(0)
    elif len(numbers) == 2 and line.find('(+)') != -1:
        numbers.append(0)  # only insertions were printed on line
    elif len(numbers) == 2 and line.find('(-)') != -1:
        numbers.insert(1, 0)  # only deletions were printed on line
    return numbers


def get_authors_info():
    authors = {}

    # Collect revision statistics
    # Outputs "<stamp> <date> <time> <timezone> <author> '<' <mail> '>'"
    lines = get_pipe_output(
        ['git rev-list --pretty=format:"%%at %%ai %%aN <%%aE>" %s' % getlogrange('HEAD'), 'grep -v ^commit']).split(
        '\n')
    for line in lines:
        parts = line.split(' ', 4)
        try:
            stamp = int(parts[0])
        except ValueError:
            stamp = 0
        author, mail = parts[4].split('<', 1)
        author = author.rstrip()
        date = datetime.datetime.fromtimestamp(float(stamp))
        # author stats
        if author not in authors:
            authors[author] = {}
        # commits, note again that commits may be in any date order because of cherry-picking and patches
        if 'last_commit_stamp' not in authors[author]:
            authors[author]['last_commit_stamp'] = stamp
        if stamp > authors[author]['last_commit_stamp']:
            authors[author]['last_commit_stamp'] = stamp
        if 'first_commit_stamp' not in authors[author]:
            authors[author]['first_commit_stamp'] = stamp
        if stamp < authors[author]['first_commit_stamp']:
            authors[author]['first_commit_stamp'] = stamp

        # authors: active days
        yymmdd = date.strftime('%Y-%m-%d')
        if 'last_active_day' not in authors[author]:
            authors[author]['last_active_day'] = yymmdd
            authors[author]['active_days'] = set([yymmdd])
        elif yymmdd != authors[author]['last_active_day']:
            authors[author]['last_active_day'] = yymmdd
            authors[author]['active_days'].add(yymmdd)

    lines = get_pipe_output(
        ['git log --shortstat --date-order --pretty=format:"%%at %%aN" %s' % (getlogrange('HEAD'))]).split('\n')
    lines.reverse()

    inserted = 0
    deleted = 0
    stamp = 0
    for line in lines:
        if len(line) == 0:
            continue
        # <stamp> <author>
        if re.search('files? changed', line) is None:
            pos = line.find(' ')
            if pos != -1:
                try:
                    oldstamp = stamp
                    (stamp, author) = (int(line[:pos]), line[pos + 1:])
                    if oldstamp > stamp:
                        # clock skew, keep old timestamp to avoid having ugly graph
                        stamp = oldstamp
                    if author not in authors:
                        authors[author] = {'lines_added': 0, 'lines_removed': 0, 'commits': 0}
                    authors[author]['commits'] = authors[author].get('commits', 0) + 1
                    authors[author]['lines_added'] = authors[author].get('lines_added', 0) + inserted
                    authors[author]['lines_removed'] = authors[author].get('lines_removed', 0) + deleted
                    files, inserted, deleted = 0, 0, 0
                except ValueError:
                    print 'Warning: unexpected line "%s"' % line
            else:
                print 'Warning: unexpected line "%s"' % line
        else:
            numbers = get_stat_summary_counts(line)
            if len(numbers) == 3:
                (files, inserted, deleted) = map(lambda el: int(el), numbers)
            else:
                print 'Warning: failed to handle line "%s"' % line
                (files, inserted, deleted) = (0, 0, 0)
    return authors


class TestPygitMethods(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        this_file_dir = os.path.dirname(os.path.abspath(__file__))
        cls.gs = GitStatistics(this_file_dir)

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

    def test_authors_info(self):
        expected_authors_dict = get_authors_info()
        actual_authors_dict = self.gs.authors
        # due to string encoding differences direct comparison of author's statistics is not possible
        self.assertEquals(len(expected_authors_dict), len(actual_authors_dict))

        # the lists of added and removed lines by authors is compared instead
        # if something is wrong in stat algo, coincidence of the numbers is highly unlikely
        expected_lines_added_list = [v['lines_added'] for (_, v) in expected_authors_dict.items()]
        actual_lines_added_list = [v['lines_added'] for (_, v) in actual_authors_dict.items()]
        self.assertListEqual(sorted(actual_lines_added_list), sorted(expected_lines_added_list))

        expected_lines_removed_list = [v['lines_removed'] for (_, v) in expected_authors_dict.items()]
        actual_lines_removed_list = [v['lines_removed'] for (_, v) in actual_authors_dict.items()]
        self.assertListEqual(sorted(actual_lines_removed_list), sorted(expected_lines_removed_list))

        expected_commits_count_list = [v['commits'] for (_, v) in expected_authors_dict.items()]
        actual_commits_count_list = [v['commits'] for (_, v) in actual_authors_dict.items()]
        self.assertListEqual(sorted(expected_commits_count_list), sorted(actual_commits_count_list))

        expected_active_days_count_list = [len(v['active_days']) for (_, v) in expected_authors_dict.items()]
        actual_active_days_count_list = [len(v['active_days']) for (_, v) in actual_authors_dict.items()]
        self.assertListEqual(sorted(expected_active_days_count_list), sorted(actual_active_days_count_list))

        expected_last_commit_stamp = [v['last_commit_stamp'] for (_, v) in expected_authors_dict.items()]
        actual_last_commit_stamp = [v['last_commit_stamp'] for (_, v) in actual_authors_dict.items()]
        self.assertListEqual(sorted(expected_last_commit_stamp), sorted(actual_last_commit_stamp))


if __name__ == '__main__':
    unittest.main()
