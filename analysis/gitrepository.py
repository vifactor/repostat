import pandas as pd
import pygit2 as git
from datetime import datetime
import pytz

from .gitdata import WholeHistory as GitWholeHistory


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
