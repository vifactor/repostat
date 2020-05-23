import pandas as pd
import pygit2 as git
import warnings
from datetime import datetime
import os
import pytz

from tools import split_email_address
from .gitdata import WholeHistory as GitWholeHistory
from .gitdata import LinearHistory as GitLinearHistory
from .gitrevision import GitRevision
from .gitauthors import GitAuthors
from .gittags import GitTags


class GitRepository:
    def __init__(self, path: str):
        """
        :param path: path to a repository
        """
        self.repo = git.Repository(path)
        self.branch = self.repo.head.shorthand
        self.whole_history_df = GitWholeHistory(self.repo).as_dataframe()
        self.linear_history_df = GitLinearHistory(self.repo).as_dataframe()
        self._head_revision = None
        self._tags = None
        self._name = None

    @property
    def name(self):
        if self._name is None:
            # remove trailing slash
            head, _ = os.path.split(self.repo.path)
            # remove '.git' subfolder
            head, _ = os.path.split(head)
            # get the folder name containing '.git'
            _, self._name = os.path.split(head)
        return self._name

    @property
    def head(self):
        if not self._head_revision:
            self._head_revision = GitRevision(self.repo, 'HEAD')
        return self._head_revision

    @property
    def tags(self):
        if not self._tags:
            self._tags = GitTags(self.repo)
        return self._tags

    @property
    def total_commits_count(self):
        return self.whole_history_df.shape[0]

    @property
    def merge_commits_count(self):
        return self.whole_history_df['is_merge_commit'].sum()

    @property
    def total_lines_added(self):
        return self.linear_history_df['insertions'].sum()

    @property
    def total_lines_removed(self):
        return self.linear_history_df['deletions'].sum()

    @property
    def total_lines_count(self):
        return self.total_lines_added - self.total_lines_removed

    @property
    def first_commit_timestamp(self):
        return self.whole_history_df["author_timestamp"].min()

    @property
    def last_commit_timestamp(self):
        return self.whole_history_df["author_timestamp"].max()

    @property
    def active_days_count(self):
        # Note, calculations here are done in UTC, calculation in local tz may give slightly different days count
        count = pd.to_datetime(self.whole_history_df['author_timestamp'], unit='s').\
            dt.strftime('%Y-%m-%d').unique().size
        return count

    @property
    def review_duration_distribution(self):
        duration_bins = [pd.Timedelta('0s').total_seconds(),
                         pd.Timedelta('1s').total_seconds(),
                         pd.Timedelta('1 hours').total_seconds(),
                         pd.Timedelta('1 day').total_seconds(),
                         pd.Timedelta('2 days').total_seconds(),
                         pd.Timedelta('1W').total_seconds(),
                         pd.Timedelta('2W').total_seconds(),
                         pd.Timedelta(30, unit='D').total_seconds(),
                         pd.Timedelta(183, unit='D').total_seconds(),
                         pd.Timedelta(3 * 365, unit='D').total_seconds()]

        review_duration_ts = self.whole_history_df['review_duration']
        review_time_binned = pd.cut(review_duration_ts, bins=duration_bins, include_lowest=True,
                                    labels=['= 0s',
                                            '< 1hour',
                                            '< 1day',
                                            '< 2days',
                                            '< 1week',
                                            '< 2weeks',
                                            '< 1month',
                                            '< 6 months',
                                            '< 3 years'
                                            ])
        return review_time_binned.value_counts().sort_index()

    @property
    def timezones_distribution(self):
        # first group commits by timezones' offset given in minutes
        ts = self.whole_history_df['author_tz_offset'].groupby(self.whole_history_df['author_tz_offset']).count()

        dummy_timestamp = pd.Timestamp(datetime.utcnow().replace(tzinfo=pytz.utc))
        # transform tz offsets (given as index of ts) in minutes to strings formatted as strftime('%z')
        # TODO: move this formatting outside of statistics
        formatted_offsets_ts = ts.reset_index(name="counts")['author_tz_offset'].apply(
            # in order to use strftime('%z') formatter, one needs to have a valid timezone aware pd.Timestamp
            # the actual date is not relevant here, so dummy timestamp is used
            lambda x: dummy_timestamp.tz_convert(pytz.FixedOffset(x)).strftime('%z'))

        # re-create series with formatted index
        return pd.Series(ts.values, index=formatted_offsets_ts.values).to_dict()

    @staticmethod
    def _fetch_domain_from_email(email):
        try:
            _, domain = split_email_address(email)
        except ValueError as ex:
            warnings.warn(str(ex))
            domain = "unknown"
        return domain

    @property
    def domains_distribution(self):
        domains_ts = self.whole_history_df['author_email'].apply(self._fetch_domain_from_email)
        return domains_ts.groupby(by=domains_ts.values).count()

    def get_recent_weekly_activity(self, recent_weeks_count: int):
        """
        Calculates contributors' weekly activity (number of commits per week)
        :param recent_weeks_count: time period in weeks
        :return: sampled number of commits
        """
        assert recent_weeks_count > 0

        today = pd.Timestamp.today()
        if today.weekday() == 6:  # 'today' is Sunday
            # set Sunday within a week as last day of recent activity ('today' is already in next week)
            last_activity_date = today + pd.Timedelta(weeks=1)
        else:
            # set last day of recent activity interval as next Monday
            last_activity_date = today + pd.Timedelta(days=-today.weekday(), weeks=1)
        # Monday `recent_weeks_count` weeks ago
        start_activity_date = last_activity_date - pd.Timedelta(weeks=recent_weeks_count)

        # TODO: committer timestamp better reflects recent activity on a current branch
        ts = pd.to_datetime(self.whole_history_df['author_timestamp'], unit='s')
        ddf = pd.DataFrame({'timestamp': ts[ts >= start_activity_date]})
        # weekly intervals
        intervals = pd.date_range(end=last_activity_date, periods=recent_weeks_count + 1, freq='W-SUN', normalize=True)
        # sample commits number by weekly intervals
        histogram = pd.cut(ddf.timestamp, bins=intervals)

        result_ts = histogram.groupby(histogram.values).count()
        return result_ts.values

    def get_authors_ranking_by_year(self):
        """
        Top authors by all years of repo existence as pandas timeseries, e.g
        timestamp  author_name
        2007       Author3        1
        2020       Author1        2
                   Author2        1

        :return: Pandas multiindex timeseries:  (<year>, <author_name>) -> <commits count>
        """
        df = pd.DataFrame({'author_name': self.whole_history_df['author_name'],
                           'timestamp': pd.to_datetime(self.whole_history_df['author_timestamp'], unit='s')})
        ts_agg = df.groupby([df.timestamp.dt.year, df.author_name]).size()
        # https://stackoverflow.com/questions/27842613/pandas-groupby-sort-within-groups
        # group by the first level of the index
        ts_agg = ts_agg.groupby(level=0, group_keys=False)
        # then sort each group
        res = ts_agg.apply(lambda x: x.sort_values(ascending=False))

        return res

    def get_authors_ranking_by_month(self):
        """
        Top authors by all month of repo existence as pandas timeseries, e.g
        timestamp  author_name
        2007-07    Author3        2
        2020-02    Author2        1
                   Author1        1

        :return: Pandas multiindex timeseries:  (<year>-<month>, <author_name>) -> <commits count>
        """

        df = pd.DataFrame({'author_name': self.whole_history_df['author_name'],
                           'timestamp': pd.to_datetime(self.whole_history_df['author_timestamp'], unit='s')
                          .dt.strftime('%Y-%m')})

        # https://stackoverflow.com/questions/27842613/pandas-groupby-sort-within-groups
        ts_agg = df.groupby([df.timestamp, df.author_name]).size()\
            .groupby(level=0, group_keys=False)

        # sort each group by value
        return ts_agg.apply(lambda x: x.sort_values(ascending=False))

    @property
    def authors(self) -> GitAuthors:
        if not hasattr(self, '_authors'):
            setattr(self, '_authors', GitAuthors(self.whole_history_df))
        return getattr(self, '_authors')

    @property
    def month_of_year_distribution(self):
        ts = pd.to_datetime(self.whole_history_df['author_timestamp'], unit='s', utc=True)
        return ts.groupby(ts.dt.month).count()

    @property
    def weekday_hour_distribution(self):
        df = self.whole_history_df[['author_timestamp']].copy()
        # Weekday activity should be calculated in local timezones
        # https://stackoverflow.com/questions/36648995/how-to-add-timezone-offset-to-pandas-datetime
        df['datetime'] = pd.to_datetime(self.whole_history_df['author_timestamp'], unit='s', utc=True) + \
                         pd.TimedeltaIndex(self.whole_history_df['author_tz_offset'], unit='m')
        df['weekday'] = df.datetime.dt.weekday
        df['hour'] = df.datetime.dt.hour

        df = df.pivot_table(
            index=df['weekday'],
            columns=df['hour'],
            values='datetime',
            aggfunc='count'
        ).fillna(0)
        return df

    def history(self, sampling):
        # this is "commits history" with timeline defined by "author_timestamp", i.e. by time when a commit was created
        df = self.whole_history_df[['author_timestamp']].copy()
        df['datetime'] = pd.to_datetime(self.whole_history_df['author_timestamp'], unit='s', utc=True)
        df = df.set_index(df['datetime'])\
            .rename(columns={'datetime': 'commits_count'})['commits_count']\
            .groupby(pd.Grouper(freq=sampling)) \
            .count()
        return df

    def linear_history(self, sampling):
        # this is "modifications history" with timeline defined by "committer_timestamp", i.e. by time when a
        # commit was incorporated (via create/amend/rebase) into branch
        df = self.linear_history_df[['committer_timestamp', 'files_count', 'insertions', 'deletions']].copy()
        df['datetime'] = pd.to_datetime(self.linear_history_df['committer_timestamp'], unit='s', utc=True)
        df = df.set_index(df['datetime'])

        wh_grouped = df[['files_count', 'insertions', 'deletions']].groupby(pd.Grouper(freq=sampling))
        result = wh_grouped[['insertions', 'deletions']].sum().cumsum()
        result['files_count'] = wh_grouped['files_count'].mean().fillna(method='ffill')
        result['lines_count'] = result['insertions'] - result['deletions']
        return result
