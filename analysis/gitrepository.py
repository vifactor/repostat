import pygit2 as git

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
