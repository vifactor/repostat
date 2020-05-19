import pygit2 as git

from tools import get_file_extension
from .gitdata import BlameData, FilesData


class GitRevision:

    def __init__(self, repository: git.Repository, revision: str = 'HEAD'):
        self.revision_df = BlameData(repository, revision).as_dataframe()
        self.files_df = FilesData(repository, revision).as_dataframe()

    @property
    def authors_contribution(self):
        return self.revision_df[["committer_name", "lines_count"]]\
            .groupby(by="committer_name")["lines_count"].sum()

    @property
    def files_count(self):
        return self.files_df["file"].unique().shape[0]

    @property
    def size(self):
        return self.files_df["size_bytes"].sum()

    @property
    def files_extensions_summary(self):
        df = self.files_df[["size_bytes", "lines_count"]]
        df["extension"] = self.files_df['file'].apply(get_file_extension)
        df = df.groupby(by="extension").agg({"size_bytes": ["sum"], "lines_count": ["sum", "count"]})
        df.columns = ["size_bytes", "lines_count", "files_count"]
        df.reset_index()
        return df.sort_values(by="files_count", ascending=False)
