import pygit2 as git


class GitStatistics:
    def __init__(self, path):
        """
        :param path: path to a repository
        """
        self.repo = git.Repository(path)
        self.authors = {}
        self.fetch_authors()

    def fetch_authors(self):
        self.authors = {commit.author.name for commit in self.repo.walk(self.repo.head.target)}