import pandas as pd
import pygit2 as git
from datetime import datetime
import pytz

from .gitdata import WholeHistory as GitWholeHistory
from .gitauthor import GitAuthor


class GitRepository(object):
    def __init__(self, path: str):
        """
        :param path: path to a repository
        """
        self.repo = git.Repository(path)
        self.whole_history_df = GitWholeHistory(self.repo).as_dataframe()

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

    def get_author(self, name: str):
        if not GitAuthor.author_groups:
            df = self.whole_history_df[['author_name', 'author_timestamp']]
            GitAuthor.author_groups = df.groupby(by='author_name')
        return GitAuthor(name)
