import abc
import pandas as pd
import pygit2 as git


class History:

    def __init__(self, repository: git.Repository, branch: str = "master"):
        self.repo = repository
        self.branch = branch
        self.cache = None

    def as_dataframe(self):
        data = self.fetch()
        return pd.DataFrame(data)

    def fetch(self):
        repo_walker = self._get_repo_walker()
        records = []
        for commit in repo_walker:
            records.append({'commit_sha': commit.hex[:7],
                            'author_tz_offset': commit.author.offset,
                            'author_timestamp': commit.author.time})
        return records

    @abc.abstractmethod
    def _get_repo_walker(self):
        pass


class WholeHistory(History):
    def _get_repo_walker(self):
        return self.repo.walk(self.repo.head.target, git.GIT_SORT_TOPOLOGICAL)


class LinearHistory(History):
    def _get_repo_walker(self):
        linear_walker = self.repo.walk(self.repo.head.target, git.GIT_SORT_TOPOLOGICAL)
        linear_walker.simplify_first_parent()
        return linear_walker
