import pygit2 as git
import pandas as pd
from typing import List, Generator
from numpy import isnan

from .gitdata import TagsData


class GitTag:

    def __init__(self, tag_df: pd.DataFrame):
        self.df_ref = tag_df

    def __repr__(self):
        return self.name

    @property
    def name(self) -> str:
        tag_name = self.df_ref.tag_name.unique()
        assert len(tag_name) == 1
        tag_name = tag_name[0]
        return tag_name if tag_name is not None else 'unreleased'

    @property
    def contributors(self) -> pd.DataFrame:
        return self.df_ref[['commit_author', 'is_merge']].groupby('commit_author')\
            .count().rename(columns={'is_merge': 'commits_count'}).sort_values(by='commits_count', ascending=False)

    @property
    def created(self):
        """
        This is tagger time, i.e. when tag as created
        :return: timestamp
        """
        ts = self.df_ref['tagger_time'].unique()
        # all tagger_time's for particular tag should be the same
        assert len(ts) == 1
        ts = ts[0]
        return pd.to_datetime(ts, unit='s', utc=True) if ts != -1 else None

    @property
    def initiated(self):
        """
        This is author's time of the very first commit that "belongs" to this tag
        :return: timestamp
        """
        return pd.to_datetime(self.df_ref['commit_time'].min(), unit='s', utc=True)

    @property
    def commits_count(self) -> int:
        """
        How many commits "belong" to this tag
        :return: commits count
        """
        return self.df_ref.shape[0]

    @property
    def tagger(self):
        tagger_name = self.df_ref['tagger_name'].unique()
        assert len(tagger_name) == 1
        tagger_name = tagger_name[0]
        return tagger_name


class GitTags:

    def __init__(self, repo: git.Repository):
        self.tags_data = TagsData(repo).as_dataframe()

    def filter(self, regexp: str) -> List[GitTag]:
        pass

    def all(self) -> 'Generator[GitTag, None]':
        return (self.get(name) for name in self.names)

    def get(self, tag_name: str) -> GitTag:
        predicate = self.tags_data.tag_name.isna() if tag_name is None else self.tags_data.tag_name == tag_name
        return GitTag(self.tags_data[predicate])

    @property
    def names(self):
        return self.tags_data.tag_name.unique()

    @property
    def count(self):
        return len(self.names)

