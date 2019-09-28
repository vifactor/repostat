import pygit2 as git
from datetime import datetime, tzinfo, timedelta
from collections import Counter
import warnings
from tools.timeit import Timeit
import os


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


class CommitDictFactory:
    AUTHOR_NAME = "author_name"
    LINES_REMOVED = "lines_removed"
    LINES_ADDED = "lines_added"
    DATE = 'date'
    TIMESTAMP = "timestamp"
    FIELD_LIST = [AUTHOR_NAME, LINES_REMOVED, LINES_ADDED, TIMESTAMP]

    @classmethod
    def create_commit(cls, author, lines_added, lines_removed, date: str, time_stamp: float):
        result = {
            cls.AUTHOR_NAME: author,
            cls.LINES_ADDED: lines_added,
            cls.LINES_REMOVED: lines_removed,
            cls.DATE: date,
            cls.TIMESTAMP: time_stamp
        }
        return result

    @classmethod
    def get_author(cls, commit_detail: dict):
        return commit_detail[cls.AUTHOR_NAME]

    @classmethod
    def get_lines_added(cls, commit_detail: dict):
        return commit_detail[cls.LINES_ADDED]

    @classmethod
    def get_lines_removed(cls, commit_detail: dict):
        return commit_detail[cls.LINES_REMOVED]

    @classmethod
    def get_time_stamp(cls, commit_detail: dict):
        return commit_detail[cls.TIMESTAMP]

    @classmethod
    def get_date(cls, commit_detail: dict):
        return commit_detail[cls.DATE]


class AuthorDictFactory:
    AUTHOR_NAME = "author_name"
    LINES_REMOVED = "lines_removed"
    LINES_ADDED = "lines_added"
    ACTIVE_DAYS = 'active_days'
    COMMITS = 'commits'
    FIRST_COMMIT = 'first_commit_stamp'
    LAST_COMMIT = 'last_commit_stamp'
    LAST_ACTIVE_DAY = 'last_active_day'
    FIELD_LIST = [AUTHOR_NAME, LINES_ADDED, LINES_REMOVED, COMMITS, ACTIVE_DAYS, FIRST_COMMIT, LAST_COMMIT,
                  LAST_ACTIVE_DAY]

    @classmethod
    def create_author(cls, author_name: str, lines_removed: int, lines_added: int, active_days: str, commits: int,
                      first_commit_stamp, last_commit_stamp):
        result = {
            cls.AUTHOR_NAME: author_name,
            cls.LINES_ADDED: lines_added,
            cls.LINES_REMOVED: lines_removed,
            cls.ACTIVE_DAYS: {active_days},
            cls.COMMITS: commits,
            cls.FIRST_COMMIT: first_commit_stamp,
            cls.LAST_COMMIT: last_commit_stamp,
            cls.LAST_ACTIVE_DAY: datetime.fromtimestamp(last_commit_stamp).strftime('%Y-%m-%d')
        }
        return result

    def _set_last_commit_stamp(self, time):
        self.last_commit_stamp = time
        # it seems that there is a mistake (or my misunderstanding) in 'last_active_day' value
        # my calculations give are not the same as those done by Heikki Hokkanen for this parameter
        self.last_active_day = datetime.fromtimestamp(time).strftime('%Y-%m-%d')

    @classmethod
    def add_active_day(cls, author, active_day):
        author[cls.ACTIVE_DAYS].add(active_day)

    @classmethod
    def add_lines_added(cls, author, lines_added):
        author[cls.LINES_ADDED] += lines_added

    @classmethod
    def add_lines_removed(cls, author, lines_removed):
        author[cls.LINES_REMOVED] += lines_removed

    @classmethod
    def add_commit(cls, author, commit_count=1):
        author[cls.COMMITS] += commit_count

    @classmethod
    def check_first_commit_stamp(cls, author: dict, time):
        if author[cls.FIRST_COMMIT] > time:
            author[cls.FIRST_COMMIT] = time

    @classmethod
    def check_last_commit_stamp(cls, author: dict, time):
        if author[cls.LAST_COMMIT] < time:
            author[cls.LAST_COMMIT] = time
            author[cls.LAST_ACTIVE_DAY] = datetime.fromtimestamp(time).strftime('%Y-%m-%d')


class GitStatistics:
    def __init__(self, path):
        """
        :param path: path to a repository
        """
        self.repo = git.Repository(path)
        self.created_time_stamp = datetime.now().timestamp()
        self.author_of_year = {}
        self.author_of_month = {}
        self.yearly_commits_timeline = {}
        self.monthly_commits_timeline = {}
        self.author_changes_history = {}
        self.commits = []
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
        self.activity_monthly, self.authors_monthly, \
            self.activity_year_monthly, self.author_year_monthly = self.fetch_monthly_activity()
        self.recent_activity_by_week = self.fetch_recent_activity()
        self.recent_activity_peak = max(activity for activity in self.recent_activity_by_week.values())
        self.changes_history, self.total_lines_added, \
            self.total_lines_removed, self.total_lines_count = self.fetch_total_history()
        self.repo_name = os.path.basename(os.path.abspath(path))

    @classmethod
    def get_fetching_tool_info(cls):
        # could be bare git-subprocess invokation, PythonGit package, etc.
        return '{} v.{}'.format(git.__name__, git.LIBGIT2_VERSION)

    def add_commit(self, author, lines_added, lines_removed, time: str, time_stamp):
        commit_details = CommitDictFactory.create_commit(author, lines_added, lines_removed, time, time_stamp)
        self.commits.append(commit_details)

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
            st = None
            if len(child_commit.parents) == 0:
                # initial commit
                st = child_commit.tree.diff_to_tree(swap=True).stats
            elif len(child_commit.parents) == 1:
                parent_commit = child_commit.parents[0]
                st = self.repo.diff(parent_commit, child_commit).stats
            else:  # if len(child_commit.parents) == 2 (merge commit)
                is_merge_commit = True

            commit_day_str = datetime.fromtimestamp(child_commit.author.time).strftime('%Y-%m-%d')

            author_name = child_commit.author.name
            lines_added = st.insertions if not is_merge_commit else 0
            lines_removed = st.deletions if not is_merge_commit else 0

            self._adjust_winners(author_name, child_commit.author.time)
            self.add_commit(author_name, lines_added, lines_removed, commit_day_str, child_commit.author.time)
            if author_name not in result:
                result[author_name] = AuthorDictFactory.create_author(
                    author_name, lines_removed, lines_added, commit_day_str, 1, child_commit.author.time,
                    child_commit.author.time)
            else:
                AuthorDictFactory.add_lines_removed(result[author_name], st.deletions if not is_merge_commit else 0)
                AuthorDictFactory.add_lines_added(result[author_name], st.insertions if not is_merge_commit else 0)
                AuthorDictFactory.add_active_day(result[author_name], commit_day_str)
                AuthorDictFactory.add_commit(result[author_name], 1)
                AuthorDictFactory.check_first_commit_stamp(result[author_name], child_commit.author.time)
                AuthorDictFactory.check_last_commit_stamp(result[author_name], child_commit.author.time)

            self._adjust_author_changes_history(child_commit, result)

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
                warnings.warn(ex)
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
        authors = {}
        activity_year_month = {}
        authors_year_month = {}
        for commit in self.repo.walk(self.repo.head.target):
            date = datetime.fromtimestamp(commit.author.time)
            month = date.month
            year_month = date.strftime('%Y-%m')
            activity[month] = activity.get(month, 0) + 1
            activity_year_month[year_month] = activity_year_month.get(year_month, 0) + 1
            try:
                authors[month].add(commit.author.name)
            except KeyError:
                authors[month] = {commit.author.name}
            try:
                authors_year_month[year_month].add(commit.author.name)
            except KeyError:
                authors_year_month[year_month] = {commit.author.name}

            self._adjust_commits_timeline(date)
        return activity, authors, activity_year_month, authors_year_month

    @Timeit("Fetching recent activity info")
    def fetch_recent_activity(self, weeks=None):
        # this returns whole activity on week basis, use the weeks argument to skip unused data
        activity = {}
        for commit in self.repo.walk(self.repo.head.target):
            date = datetime.fromtimestamp(commit.author.time)
            yyw = date.strftime('%Y-%W')
            if weeks is None:
                activity[yyw] = activity.get(yyw, 0) + 1
            elif yyw in weeks:
                activity[yyw] = activity.get(yyw, 0) + 1

        return activity

    @staticmethod
    def build_history_item(child_commit, stat) -> dict:
        return {
            'files': stat.files_changed,
            'ins': stat.insertions,
            'del': stat.deletions,
            'author': child_commit.author.name,
            'author_mail': child_commit.author.email,
            'is_merge': len(child_commit.parents) > 1,
            'commit_time': child_commit.commit_time,
            'oid': child_commit.oid,
            'parent_ids': child_commit.parent_ids
        }

    @Timeit("Fetching total history")
    def fetch_total_history(self):
        history = {}
        child_commit = self.repo.head.peel()
        timestamps = []
        while len(child_commit.parents) != 0:
            # taking [0]-parent is equivalent of '--first-parent -m' options
            parent_commit = child_commit.parents[0]
            st = self.repo.diff(parent_commit, child_commit).stats
            history[child_commit.author.time] = self.build_history_item(child_commit, st)
            timestamps.append(child_commit.author.time)
            child_commit = parent_commit
        # initial commit does not have parent, so we take diff to empty tree
        st = child_commit.tree.diff_to_tree(swap=True).stats
        history[child_commit.author.time] = self.build_history_item(child_commit, st)

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

    def _adjust_author_changes_history(self, commit, authors_info: dict):
        ts = commit.author.time

        author_name = commit.author.name
        if ts not in self.author_changes_history:
            self.author_changes_history[ts] = {}
        if author_name not in self.author_changes_history[ts]:
            self.author_changes_history[ts][author_name] = {}
        self.author_changes_history[ts][author_name]['lines_added'] = authors_info[author_name][
            AuthorDictFactory.LINES_ADDED]
        self.author_changes_history[ts][author_name]['commits'] = authors_info[author_name][AuthorDictFactory.COMMITS]

    def _adjust_commits_timeline(self, datetime_obj):
        """
        increments commit count into the corresponding dicts gathering yearly/monthly commits' history
        :param datetime_obj: a datetime object of a commit
        """
        yymm = datetime_obj.strftime('%Y-%m')
        self.monthly_commits_timeline[yymm] = self.monthly_commits_timeline.get(yymm, 0) + 1

        yy = datetime_obj.year
        self.yearly_commits_timeline[yy] = self.yearly_commits_timeline.get(yy, 0) + 1

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

    def get_commit_delta_days(self):
        return (self.last_commit_timestamp / 86400 - self.first_commit_timestamp / 86400) + 1

    def get_active_days(self):
        return self.active_days

    def get_total_line_count(self):
        return self.total_lines_count

    def get_total_authors(self):
        return self.authors.__len__()

    def get_total_commits(self):
        return self.commits.__len__()

    def get_stamp_created(self):
        return self.created_time_stamp

    # TODO: Implementation
    @staticmethod
    def get_total_files():
        return 0
