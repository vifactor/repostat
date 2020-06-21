import pygit2 as git
import pandas as pd

from tools import get_file_extension
from .gitdata import BlameData, FilesData


class GitRevision:

    def __init__(self, repository: git.Repository, revision: str = 'HEAD'):
        self.blame_data = BlameData(repository, revision)
        self.files_data = FilesData(repository, revision).as_dataframe()

    def _lazy_load_blame_data(self):
        # replaces class with raw DataFrame this class supposes to fetch
        if isinstance(self.blame_data, BlameData):
            self.blame_data = self.blame_data.as_dataframe()

    @property
    def authors_contribution(self):
        self._lazy_load_blame_data()
        return self.blame_data[["committer_name", "lines_count"]]\
            .groupby(by="committer_name")["lines_count"].sum()

    def get_top_files_by_contributors_count(self, top_size=10):
        self._lazy_load_blame_data()
        return self.blame_data[["committer_name", "filepath"]].groupby(["filepath"])\
            .committer_name.nunique().sort_values(ascending=False).head(top_size)

    @property
    def monoauthor_files(self):
        self._lazy_load_blame_data()
        committer_per_file = self.blame_data[["committer_name", "filepath"]].groupby(["filepath"])\
            .committer_name.nunique()
        return committer_per_file[committer_per_file == 1]

    def get_lost_knowledge_percentage(self, knowledge_loss_period_month=6):
        """
        Metrics is introduced in:
        https://www.feststelltaste.de/identifying-lost-knowledge-in-the-linux-kernel-source-code/

        :param knowledge_loss_period_month: months count after which code knowledge is considered to be "lost"
        :return: the ratio of known code to unknown code (= code older than `knowledge_loss_period_month` months)
        """
        self._lazy_load_blame_data()
        months_ago = pd.Timestamp.utcnow() - pd.DateOffset(months=knowledge_loss_period_month)
        df = self.blame_data[["lines_count", "timestamp"]].copy()
        df.timestamp = pd.to_datetime(df.timestamp, unit='s', utc=True)
        df['knowing'] = df.timestamp >= months_ago
        total_lines_count = df.lines_count.sum()
        forgotten_lines_count = df[~df.knowing].lines_count.astype('float').sum()
        return forgotten_lines_count / total_lines_count

    def get_top_knowledge_carriers(self, knowledge_loss_period_month=6):
        """
        Metrics is introduced in:
        https://www.feststelltaste.de/identifying-lost-knowledge-in-the-linux-kernel-source-code/

        :param knowledge_loss_period_month: months count after which code knowledge is considered to be "lost"
        :return: dataframe of contributors with lines count contributed in last `knowledge_loss_period_month`
        """
        self._lazy_load_blame_data()
        months_ago = pd.Timestamp.utcnow() - pd.DateOffset(months=knowledge_loss_period_month)
        df = self.blame_data[["lines_count", "timestamp", 'committer_name']].copy()
        df.timestamp = pd.to_datetime(df.timestamp, unit='s', utc=True)
        df['knowing'] = df.timestamp >= months_ago

        res = df[df.knowing].groupby("committer_name").agg({"lines_count": 'sum'}).reset_index()

        # this step is needed because `committer_name` is categorical and all authors appear to be present
        # in grouped dataframe with zero contribution
        recent_contributors = df[df.knowing].committer_name.unique()
        res = res[res.committer_name.isin(recent_contributors)].sort_values(by="lines_count", ascending=False)\
            .reset_index(drop=True)

        return res

    @property
    def files_count(self):
        return self.files_data["file"].unique().shape[0]

    @property
    def size(self):
        return self.files_data["size_bytes"].sum()

    @property
    def files_extensions_summary(self):
        df = self.files_data[["is_binary", "size_bytes", "lines_count"]].copy()
        df["extension"] = self.files_data['file'].apply(get_file_extension)
        df = df.groupby(by=["is_binary", "extension"]).agg({"size_bytes": ["sum"], "lines_count": ["sum", "count"]})
        df.columns = ["size_bytes", "lines_count", "files_count"]
        df.reset_index()

        return df
