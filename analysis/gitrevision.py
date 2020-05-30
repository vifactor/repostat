import pygit2 as git

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

    @property
    def files_count(self):
        return self.files_data["file"].unique().shape[0]

    @property
    def size(self):
        return self.files_data["size_bytes"].sum()

    @property
    def files_extensions_summary(self):
        df = self.files_data[["size_bytes", "lines_count"]]
        df["extension"] = self.files_data['file'].apply(get_file_extension)
        df = df.groupby(by="extension").agg({"size_bytes": ["sum"], "lines_count": ["sum", "count"]})
        df.columns = ["size_bytes", "lines_count", "files_count"]
        df.reset_index()

        # Group together all extensions used only once (probably not really extensions)
        is_orphan = df["files_count"] <= 1
        excluded = df[is_orphan]
        result = df[~is_orphan]
        df = result.sort_values(by="files_count", ascending=False)
        #return df.append(excluded.agg({"size_bytes": ["sum"], "lines_count": ["sum", "count"]})
        return df
