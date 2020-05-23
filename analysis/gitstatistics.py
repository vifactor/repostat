import pygit2 as git
from datetime import datetime
import warnings
import os

from tools.timeit import Timeit


class GitStatistics:
    def __init__(self, path):
        """
        :param path: path to a repository
        """
        self.repo = git.Repository(path)

        self.repo_name = os.path.basename(os.path.abspath(path))
        self.analysed_branch = self.repo.head.shorthand
