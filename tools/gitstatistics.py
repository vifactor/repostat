from __future__ import unicode_literals
from __future__ import absolute_import
import pygit2 as git
from datetime import datetime, tzinfo, timedelta
from collections import Counter
import warnings
from .timeit import Timeit
from six.moves import filter


class FixedOffset(tzinfo):
    """Fixed offset in minutes east from UTC."""

    def __init__(self, offset):
        self.__offset = timedelta(minutes=offset)

    def utcoffset(self, dt):
        return self.__offset

    def tzname(self, dt):
        # we don't know the time zone's name
        return None

    def dst(self, dt):
        # we don't know about DST
        return timedelta(0)


def split_email_address(email_address):
    parts = email_address.split('@')
    if len(parts) != 2:
        raise ValueError('Not an email passed: %s' % email_address)
    return parts[0], parts[1]


class GitStatistics:
    def __init__(self, path):
        """
        :param path: path to a repository
        """
        self.repo = git.Repository(path)
        self.author_of_year = {}
        self.author_of_month = {}
        self.yearly_commits_timeline = {}
        self.monthly_commits_timeline = {}
        self.author_changes_history = {}
        self.authors = self.fetch_authors_info()
        self.tags = self.fetch_tags_info()
        self.domains = self.fetch_domains_info()
        self.timezones = self.fetch_timezone_info()
        self.first_commit_timestamp = min(commit.author.time for commit in self.repo.walk(self.repo.head.target))
        self.last_commit_timestamp = max(commit.author.time for commit in self.repo.walk(self.repo.head.target))
        self.active_days = {datetime.fromtimestamp(commit.author.time).strftime('%Y-%m-%d')
                            for commit in self.repo.walk(self.repo.head.target)}
        self.activity_weekly_hourly = self.fetch_weekly_hourly_activity()
        self.max_weekly_hourly_activity = max(
            commits_count for _, hourly_activity in self.activity_weekly_hourly.items()
            for _, commits_count in hourly_activity.items())
        self.activity_monthly = self.fetch_monthly_activity()
        self.recent_activity_by_week = self.fetch_recent_activity()
        self.recent_activity_peak = max(activity for activity in self.recent_activity_by_week.values())
        self.changes_history, self.total_lines_added, self.total_lines_removed, self.total_lines_count \
            = self.fetch_total_history()

    @classmethod
    def get_fetching_tool_info(cls):
        # could be bare git-subprocess invokation, PythonGit package, etc.
        return '{} v.{}'.format(git.__name__, git.LIBGIT2_VERSION)

    @Timeit("Fetching authors info")
    def fetch_authors_info(self):
        """
        e.g.
        {'Stefano Mosconi': {'lines_removed': 1, 'last_commit_stamp': 1302027851, 'active_days': set(['2011-04-05']),
                             'lines_added': 1, 'commits': 1, 'first_commit_stamp': 1302027851,
                             'last_active_day': '2011-04-05'}
        """
        result = {}
        for child_commit in self.repo.walk(self.repo.head.target, git.GIT_SORT_TIME | git.GIT_SORT_REVERSE):
            is_merge_commit = False
            if len(child_commit.parents) == 0:
                # initial commit
                st = child_commit.tree.diff_to_tree(swap=True).stats
            elif len(child_commit.parents) == 1:
                parent_commit = child_commit.parents[0]
                st = self.repo.diff(parent_commit, child_commit).stats
            else:  # if len(child_commit.parents) == 2 (merge commit)
                is_merge_commit = True
            commit_day_str = datetime.fromtimestamp(child_commit.author.time).strftime('%Y-%m-%d')
            author_name = child_commit.author.name.encode('utf-8')
            self._adjust_winners(author_name, child_commit.author.time)
            if author_name not in result:
                result[author_name] = {
                    'lines_removed': st.deletions if not is_merge_commit else 0,
                    'lines_added': st.insertions if not is_merge_commit else 0,
                    'active_days': {commit_day_str},
                    'commits': 1,
                    'first_commit_stamp': child_commit.author.time,
                    'last_commit_stamp': child_commit.author.time,
                }
            else:
                result[author_name]['lines_removed'] += st.deletions if not is_merge_commit else 0
                result[author_name]['lines_added'] += st.insertions if not is_merge_commit else 0
                result[author_name]['active_days'].add(commit_day_str)
                result[author_name]['commits'] += 1
                if result[author_name]['first_commit_stamp'] > child_commit.author.time:
                    result[author_name]['first_commit_stamp'] = child_commit.author.time
                if result[author_name]['last_commit_stamp'] < child_commit.author.time:
                    result[author_name]['last_commit_stamp'] = child_commit.author.time
            self._adjust_author_changes_history(child_commit, result)

        # it seems that there is a mistake (or my misunderstanding) in 'last_active_day' value
        # my calculations give are not the same as those done by Heikki Hokkanen for this parameter
        for author in result:
            last_active_day = datetime.fromtimestamp(result[author]['last_commit_stamp']).strftime('%Y-%m-%d')
            result[author]['last_active_day'] = last_active_day

        return result

    @Timeit("Fetching tags info")
    def fetch_tags_info(self):
        tags = [refobj for refobj in self.repo.listall_reference_objects() if refobj.name.startswith('refs/tags')]
        commit_tag = {refobj.peel().oid: refobj.shorthand for refobj in tags}

        result = {refobj.shorthand: {
            'stamp': refobj.peel().author.time,
            'date': datetime.fromtimestamp(refobj.peel().author.time).strftime('%Y-%m-%d'),
            'hash': str(refobj.target)} for refobj in tags}

        authors = {}
        commit_count = 0
        for commit in self.repo.walk(self.repo.head.target, git.GIT_SORT_TOPOLOGICAL | git.GIT_SORT_REVERSE):
            commit_count += 1
            authors[commit.author.name] = authors.get(commit.author.name, 0) + 1
            if commit.oid in commit_tag.keys():
                tagname = commit_tag[commit.oid]
                result[tagname]['commits'] = commit_count
                result[tagname]['authors'] = authors

                commit_count = 0
                authors = {}

        return result

    @Timeit("Fetching domains info")
    def fetch_domains_info(self):
        result = {}
        for commit in self.repo.walk(self.repo.head.target):
            try:
                _, domain = split_email_address(commit.author.email)
                result[domain] = result.get(domain, 0) + 1
            except ValueError as ex:
                warnings.warn(ex.message)
        # TODO: this is done to save compatibility with gitstats' structures
        result = {k: {'commits': v} for k, v in result.items()}
        return result

    @Timeit("Fetching timezone info")
    def fetch_timezone_info(self):
        result = {}
        for commit in self.repo.walk(self.repo.head.target):
            # hint from https://github.com/libgit2/pygit2/blob/master/docs/recipes/git-show.rst
            tz = FixedOffset(commit.author.offset)
            dt = datetime.fromtimestamp(float(commit.author.time), tz)
            timezone_str = dt.strftime('%z')
            result[timezone_str] = result.get(timezone_str, 0) + 1
        return result

    @Timeit("Fetching weekly/hourly activity info")
    def fetch_weekly_hourly_activity(self):
        activity = {}
        for commit in self.repo.walk(self.repo.head.target):
            date = datetime.fromtimestamp(commit.author.time)
            hour = date.hour
            weekday = date.weekday()
            if weekday not in activity:
                activity[weekday] = {}
            activity[weekday][hour] = activity[weekday].get(hour, 0) + 1
        return activity

    @Timeit("Fetching monthly activity info")
    def fetch_monthly_activity(self):
        activity = {}
        for commit in self.repo.walk(self.repo.head.target):
            date = datetime.fromtimestamp(commit.author.time)
            month = date.month
            activity[month] = activity.get(month, 0) + 1
            self._adjust_commits_timeline(date)
        return activity

    @Timeit("Fetching recent activity info")
    def fetch_recent_activity(self, weeks=None):
        # FIXME: so far this returns whole activity on week basis, use the weeks argument to skip unused data
        activity = {}
        for commit in self.repo.walk(self.repo.head.target):
            date = datetime.fromtimestamp(commit.author.time)
            yyw = date.strftime('%Y-%W')
            activity[yyw] = activity.get(yyw, 0) + 1
        return activity

    @Timeit("Fetching total history")
    def fetch_total_history(self):
        history = {}
        child_commit = self.repo.head.peel()
        timestamps = []
        while len(child_commit.parents) != 0:
            # taking [0]-parent is equivalent of '--first-parent -m' options
            parent_commit = child_commit.parents[0]
            st = self.repo.diff(parent_commit, child_commit).stats
            history[child_commit.author.time] = {'files': st.files_changed,
                                                 'ins': st.insertions,
                                                 'del': st.deletions}
            timestamps.append(child_commit.author.time)
            child_commit = parent_commit
        # initial commit does not have parent, so we take diff to empty tree
        st = child_commit.tree.diff_to_tree(swap=True).stats
        history[child_commit.author.time] = {'files': st.files_changed,
                                             'ins': st.insertions,
                                             'del': st.deletions}
        timestamps.append(child_commit.author.time)

        lines_count = 0
        lines_added = 0
        lines_removed = 0
        timestamps.reverse()
        for t in timestamps:
            lines_added += history[t]['ins']
            lines_removed += history[t]['del']
            lines_count += history[t]['ins'] - history[t]['del']
            history[t]['lines'] = lines_count
        return history, lines_added, lines_removed, lines_count

    def get_weekly_activity(self):
        return {weekday: sum(commits_count for commits_count in hourly_activity.values())
                for weekday, hourly_activity in self.activity_weekly_hourly.items()}

    def get_hourly_activity(self):
        activity = {}
        for hourly_activity in self.activity_weekly_hourly.values():
            for hour, commits_count in hourly_activity.items():
                activity[hour] = activity.get(hour, 0) + commits_count
        return activity

    # FIXME: although being 'pythonic', next four methods do not seem to be effective
    def get_lines_insertions_by_year(self):
        res = sum((Counter({datetime.fromtimestamp(ts).year: data['ins']})
                   for ts, data in self.changes_history.items()), Counter())
        return dict(res)

    def get_lines_deletions_by_year(self):
        res = sum((Counter({datetime.fromtimestamp(ts).year: data['del']})
                   for ts, data in self.changes_history.items()), Counter())
        return dict(res)

    def get_lines_insertions_by_month(self):
        res = sum((Counter({datetime.fromtimestamp(ts).strftime('%Y-%m'): data['ins']})
                   for ts, data in self.changes_history.items()), Counter())
        return dict(res)

    def get_lines_deletions_by_month(self):
        res = sum((Counter({datetime.fromtimestamp(ts).strftime('%Y-%m'): data['del']})
                   for ts, data in self.changes_history.items()), Counter())
        return dict(res)

    def _adjust_winners(self, author, timestamp):
        date = datetime.fromtimestamp(timestamp)
        yymm = date.strftime('%Y-%m')
        if yymm in self.author_of_month:
            self.author_of_month[yymm][author] = self.author_of_month[yymm].get(author, 0) + 1
        else:
            self.author_of_month[yymm] = {author: 1}

        yy = date.year
        if yy in self.author_of_year:
            self.author_of_year[yy][author] = self.author_of_year[yy].get(author, 0) + 1
        else:
            self.author_of_year[yy] = {author: 1}

    def _adjust_author_changes_history(self, commit, authors_info):
        ts = commit.author.time
        author_name = commit.author.name.encode('utf-8')
        if ts not in self.author_changes_history:
            self.author_changes_history[ts] = {}
        if author_name not in self.author_changes_history[ts]:
            self.author_changes_history[ts][author_name] = {}
        self.author_changes_history[ts][author_name]['lines_added'] = authors_info[author_name]['lines_added']
        self.author_changes_history[ts][author_name]['commits'] = authors_info[author_name]['commits']

    def _adjust_commits_timeline(self, datetime_obj):
        """
        increments commit count into the corresponding dicts gathering yearly/monthly commits' history
        :param datetime_obj: a datetime object of a commit
        """
        yymm = datetime_obj.strftime('%Y-%m')
        self.monthly_commits_timeline[yymm] = self.monthly_commits_timeline.get(yymm, 0) + 1

        yy = datetime_obj.year
        self.yearly_commits_timeline[yy] = self.yearly_commits_timeline.get(yy, 0) + 1

    def get_files_info(self, revision):
        """
        :param revision: revision id
        :return: pygit2.Diff for a given revision
        """
        obj = self.repo.revparse_single(revision)
        diff = None
        if isinstance(obj, git.Tree):
            diff = obj.diff_to_tree()
        elif isinstance(obj, git.Commit):
            diff = obj.tree.diff_to_tree()

        return diff

    def get_total_size(self, revision='HEAD'):
        # FIXME: not the most elegant and effective function
        # TODO: check how it works for submodules
        tree = self.repo.revparse_single(revision)
        if isinstance(tree, git.Commit):
            tree = tree.tree
        s = [tree]
        res = 0
        while s:
            for entry in s.pop():
                if entry.type == 'blob':
                    res += self.repo[entry.id].size
                elif entry.type == 'tree':
                    s.append(self.repo[entry.id])
        return res

    # TODO: too low level function for a GitStatistics class. Needed for fastest migration to pygit2
    def get_revisions(self):
        for commit in self.repo.walk(self.repo.head.target, git.GIT_SORT_TIME):
            yield commit.author.time, commit.tree_id.hex
