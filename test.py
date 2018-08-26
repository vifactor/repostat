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


def get_domain_info():
    domains = {}
    lines = get_pipe_output(
        ['git rev-list --pretty=format:"%%at %%ai %%aN <%%aE>" %s' % getlogrange('HEAD'), 'grep -v ^commit']).split(
        '\n')
    for line in lines:
        parts = line.split(' ', 4)
        author, mail = parts[4].split('<', 1)
        mail = mail.rstrip('>')
        domain = '?'
        if mail.find('@') != -1:
            domain = mail.rsplit('@', 1)[1]

        domain = domain.decode('utf-8')
        # domain stats
        if domain not in domains:
            domains[domain] = {}
        # commits
        domains[domain]['commits'] = domains[domain].get('commits', 0) + 1

    return domains


def get_timezone_info():
    timezones = {}
    lines = get_pipe_output(
        ['git rev-list --pretty=format:"%%at %%ai %%aN <%%aE>" %s' % getlogrange('HEAD'), 'grep -v ^commit']).split(
        '\n')
    for line in lines:
        parts = line.split(' ', 4)
        timezone = parts[3]
        timezones[timezone] = timezones.get(timezone, 0) + 1

    return timezones


def get_active_days_info():
    active_days = set()
    lines = get_pipe_output(
        ['git rev-list --pretty=format:"%%at %%ai %%aN <%%aE>" %s' % getlogrange('HEAD'), 'grep -v ^commit']).split(
        '\n')
    for line in lines:
        parts = line.split(' ', 4)
        try:
            stamp = int(parts[0])
        except ValueError:
            stamp = 0
        date = datetime.datetime.fromtimestamp(float(stamp))
        yymmdd = date.strftime('%Y-%m-%d')
        # project: active days
        active_days.add(yymmdd)

    return active_days


def get_winners_info():
    aom = {}
    aoy = {}
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

        # author of the month/year
        yymm = date.strftime('%Y-%m')
        if yymm in aom:
            aom[yymm][author] = aom[yymm].get(author, 0) + 1
        else:
            aom[yymm] = {}
            aom[yymm][author] = 1

        yy = date.year
        if yy in aoy:
            aoy[yy][author] = aoy[yy].get(author, 0) + 1
        else:
            aoy[yy] = {}
            aoy[yy][author] = 1
    return aom, aoy


def get_weekly_hourly_activity():
    activity_by_hour_of_week = {}
    activity_by_hour_of_week_busiest = 0
    lines = get_pipe_output(
        ['git rev-list --pretty=format:"%%at %%ai %%aN <%%aE>" %s' % getlogrange('HEAD'), 'grep -v ^commit']).split(
        '\n')
    for line in lines:
        parts = line.split(' ', 4)
        try:
            stamp = int(parts[0])
        except ValueError:
            stamp = 0
        date = datetime.datetime.fromtimestamp(float(stamp))

        # activity
        # hour
        hour = date.hour
        # day of week
        day = date.weekday()

        # hour of week
        if day not in activity_by_hour_of_week:
            activity_by_hour_of_week[day] = {}
        activity_by_hour_of_week[day][hour] = activity_by_hour_of_week[day].get(hour, 0) + 1
        # most active hour?
        if activity_by_hour_of_week[day][hour] > activity_by_hour_of_week_busiest:
            activity_by_hour_of_week_busiest = activity_by_hour_of_week[day][hour]

    return activity_by_hour_of_week, activity_by_hour_of_week_busiest


def get_monthly_activity_info():
    activity_by_month_of_year = {}
    lines = get_pipe_output(
        ['git rev-list --pretty=format:"%%at %%ai %%aN <%%aE>" %s' % getlogrange('HEAD'), 'grep -v ^commit']).split(
        '\n')
    for line in lines:
        parts = line.split(' ', 4)
        try:
            stamp = int(parts[0])
        except ValueError:
            stamp = 0
        date = datetime.datetime.fromtimestamp(float(stamp))

        # activity
        # month of year
        month = date.month
        activity_by_month_of_year[month] = activity_by_month_of_year.get(month, 0) + 1

    return activity_by_month_of_year


def get_commits_count_change_timeline():
    commits_by_month = {}
    commits_by_year = {}
    lines = get_pipe_output(
        ['git rev-list --pretty=format:"%%at %%ai %%aN <%%aE>" %s' % getlogrange('HEAD'), 'grep -v ^commit']).split(
        '\n')
    for line in lines:
        parts = line.split(' ', 4)
        try:
            stamp = int(parts[0])
        except ValueError:
            stamp = 0
        date = datetime.datetime.fromtimestamp(float(stamp))
        yymm = date.strftime('%Y-%m')
        commits_by_month[yymm] = commits_by_month.get(yymm, 0) + 1

        yy = date.year
        commits_by_year[yy] = commits_by_year.get(yy, 0) + 1

    return commits_by_month, commits_by_year


def get_activity_by_year_week():
    activity_by_year_week = {}
    activity_by_year_week_peak = 0
    lines = get_pipe_output(
        ['git rev-list --pretty=format:"%%at %%ai %%aN <%%aE>" %s' % getlogrange('HEAD'), 'grep -v ^commit']).split('\n')
    for line in lines:
        parts = line.split(' ', 4)
        try:
            stamp = int(parts[0])
        except ValueError:
            stamp = 0
        date = datetime.datetime.fromtimestamp(float(stamp))

        # activity
        # yearly/weekly activity
        yyw = date.strftime('%Y-%W')
        activity_by_year_week[yyw] = activity_by_year_week.get(yyw, 0) + 1
        if activity_by_year_week_peak < activity_by_year_week[yyw]:
            activity_by_year_week_peak = activity_by_year_week[yyw]
    return activity_by_year_week, activity_by_year_week_peak


def get_total_changes_timeline():
    # line statistics
    # outputs:
    #  N files changed, N insertions (+), N deletions(-)
    # <stamp> <author>
    changes_by_date = {}  # stamp -> { files, ins, del }
    lines_added_by_month = {}
    lines_removed_by_month = {}
    lines_added_by_year = {}
    lines_removed_by_year = {}
    total_lines_added = 0
    total_lines_removed = 0
    # computation of lines of code by date is better done
    # on a linear history.
    extra = ''
    if conf['linear_linestats']:
        extra = '--first-parent -m'
    lines = get_pipe_output(
        ['git log --shortstat %s --pretty=format:"%%at %%aN" %s' % (extra, getlogrange('HEAD'))]).split('\n')
    lines.reverse()
    files = 0
    inserted = 0
    deleted = 0
    total_lines = 0
    for line in lines:
        if len(line) == 0:
            continue
        # <stamp> <author>
        if re.search('files? changed', line) is None:
            pos = line.find(' ')
            if pos != -1:
                try:
                    (stamp, author) = (long(line[:pos]), line[pos + 1:])
                    changes_by_date[stamp] = {u'files': files, u'ins': inserted, u'del': deleted, u'lines': total_lines}

                    date = datetime.datetime.fromtimestamp(stamp)
                    yymm = date.strftime('%Y-%m')
                    lines_added_by_month[yymm] = lines_added_by_month.get(yymm, 0) + inserted
                    lines_removed_by_month[yymm] = lines_removed_by_month.get(yymm, 0) + deleted

                    yy = date.year
                    lines_added_by_year[yy] = lines_added_by_year.get(yy, 0) + inserted
                    lines_removed_by_year[yy] = lines_removed_by_year.get(yy, 0) + deleted

                    files, inserted, deleted = 0, 0, 0
                except ValueError:
                    print 'Warning: unexpected line "%s"' % line
            else:
                print 'Warning: unexpected line "%s"' % line
        else:
            numbers = get_stat_summary_counts(line)
            if len(numbers) == 3:
                (files, inserted, deleted) = map(lambda el: int(el), numbers)
                total_lines += inserted
                total_lines -= deleted
                total_lines_added += inserted
                total_lines_removed += deleted
            else:
                print 'Warning: failed to handle line "%s"' % line
                (files, inserted, deleted) = (0, 0, 0)
    return changes_by_date, total_lines_added, total_lines_removed


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

    def test_domain_info(self):
        expected_domain_info = get_domain_info()
        actual_domain_info = self.gs.domains
        for do, co in expected_domain_info.items():
            self.assertEquals(actual_domain_info[do]['commits'], co['commits'])

    def test_timezone_info(self):
        expected_timezone_info = get_timezone_info()
        actual_timezone_info = self.gs.timezones
        self.assertDictEqual(expected_timezone_info, actual_timezone_info)

    def test_active_days_info(self):
        expected_active_days = get_active_days_info()
        self.assertEquals(expected_active_days, self.gs.active_days)

    def test_winners_info(self):
        expected_aom_dict, expected_aoy_dict = get_winners_info()
        self.assertEquals(self.gs.author_of_month, expected_aom_dict)
        self.assertEquals(self.gs.author_of_year, expected_aoy_dict)

    def test_activity_weekly_hourly(self):
        expected_activity, expected_commits_count_in_busiest_weekday_hour = get_weekly_hourly_activity()
        self.assertDictEqual(expected_activity, self.gs.activity_weekly_hourly)
        self.assertEquals(expected_commits_count_in_busiest_weekday_hour, self.gs.max_weekly_hourly_activity)

    def test_activity_weekly(self):
        # TODO: manually checked
        print self.gs.get_weekly_activity()

    def test_activity_hourly(self):
        # TODO: manually checked
        print self.gs.get_hourly_activity()

    def test_activity_monthly(self):
        expected_monthly_activity = get_monthly_activity_info()
        self.assertDictEqual(expected_monthly_activity, self.gs.activity_monthly)

    def test_commits_count_change(self):
        expected_by_month, expected_by_year = get_commits_count_change_timeline()
        self.assertDictEqual(expected_by_month, self.gs.monthly_commits_timeline)
        self.assertDictEqual(expected_by_year, self.gs.yearly_commits_timeline)

    def test_recent_by_week_activity(self):
        expected_activity, expected_activity_peak = get_activity_by_year_week()
        self.assertDictEqual(expected_activity, self.gs.recent_activity_by_week)
        self.assertEquals(expected_activity_peak, self.gs.recent_activity_peak)

    def test_changes_history(self):
        expected_history, tla, tlr = get_total_changes_timeline()
        for t, expected_record in expected_history.iteritems():
            self.assertDictEqual(expected_record, self.gs.changes_history[t], "{}: {} vs. {}".format(
                t, expected_record, self.gs.changes_history[t]))
        self.assertEquals(tla, self.gs.total_lines_added)
        self.assertEquals(tlr, self.gs.total_lines_removed)

if __name__ == '__main__':
    unittest.main()
