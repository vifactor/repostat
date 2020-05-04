import pandas as pd


class GitAuthors(object):
    def __init__(self, git_history: pd.DataFrame):
        self.raw_authors_data = git_history[['author_name',
                                             'is_merge_commit',
                                             'insertions',
                                             'deletions']].copy()
        self.raw_authors_data['author_datetime'] = pd.to_datetime(git_history['author_timestamp'], unit='s', utc=True)

        authors_grouped = self.raw_authors_data[['author_name', 'author_datetime',
                                                 'insertions', 'deletions', 'is_merge_commit']].groupby(
            [self.raw_authors_data['author_name']])
        self.authors_summary = authors_grouped.sum()
        self.authors_summary['first_commit_date'] = authors_grouped['author_datetime'].min()
        self.authors_summary['latest_commit_date'] = authors_grouped['author_datetime'].max()
        self.authors_summary['active_days_count'] = authors_grouped['author_datetime'] \
            .apply(lambda g: g.dt.normalize().unique().shape[0])
        self.authors_summary['contributed_days_count'] = (self.authors_summary['latest_commit_date']
                                                          - self.authors_summary['first_commit_date']).dt.days
        # if contributor did commits in one day, difference in days between latest and first commit is 0
        # next string fixed this issue by replacing 0 with 1
        self.authors_summary['contributed_days_count'].replace(0, 1, inplace=True)
        self.authors_summary['commits_count'] = authors_grouped['author_name'].count()
        self.authors_summary.rename(columns={'is_merge_commit': 'merge_commits_count'}, inplace=True)
        self.authors_summary['merge_commits_count'] = self.authors_summary['merge_commits_count'].astype('int32')
        self.authors_summary.reset_index(inplace=True)

    def count(self):
        return self.authors_summary.shape[0]

    def names(self):
        return self.authors_summary['author_name'].values

    def sort(self, by="commits_count"):
        self.authors_summary = self.authors_summary.sort_values(by=by, ascending=False)
        return self

    def get(self, name):
        # TODO: this should produce GitAuthor object
        return self.authors_summary.loc[self.authors_summary['author_name'] == name]

    @property
    def summary(self):
        return self.authors_summary

    def history(self, sampling):
        """
        :param sampling: frequency string https://pandas.pydata.org/pandas-docs/stable/user_guide/timeseries.html#offset-aliases
        :return: Dataframe with Datetime multiindexindex and changes history data by authors
        """
        wh = self.raw_authors_data[['author_name', 'insertions', 'deletions', 'author_datetime']].copy()
        wh = wh.set_index(wh['author_datetime'])
        wh_grouped = wh[['author_name', 'insertions', 'deletions']].groupby(
            [wh['author_name'], pd.Grouper(freq=sampling)])

        modifications_over_time = wh_grouped.sum()\
            .reset_index()

        commits_over_time = wh_grouped.count().rename(columns={'author_name': 'commits_count'})\
            .reset_index()

        modifications_over_time['commits_count'] = commits_over_time['commits_count']

        modifications_per_author_over_time = modifications_over_time.reset_index().pivot_table(
            index=modifications_over_time['author_datetime'],
            columns=modifications_over_time['author_name'],
            values=['insertions', 'deletions', 'commits_count']).fillna(0)
        return modifications_per_author_over_time
