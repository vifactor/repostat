import pygit2 as git
import datetime

class GitStatistics:
    def __init__(self, path):
        """
        :param path: path to a repository
        """
        self.repo = git.Repository(path)
        self.authors = self.fetch_authors()
        self.tags = self.fetch_tags_info()

    def fetch_authors(self):
        return {commit.author.name for commit in self.repo.walk(self.repo.head.target)}

    def fetch_tags_info(self):
        tags = filter(lambda refobj: refobj.name.startswith('refs/tags'), self.repo.listall_reference_objects())
        commit_tag = {refobj.peel().oid: refobj.shorthand for refobj in tags}

        result = {refobj.shorthand: {
            'stamp': refobj.peel().author.time,
            'date': datetime.datetime.fromtimestamp(refobj.peel().author.time).strftime('%Y-%m-%d'),
            'hash': str(refobj.target)} for refobj in tags}

        authors = {}
        commit_count = 0
        for commit in self.repo.walk(self.repo.head.target, git.GIT_SORT_TOPOLOGICAL | git.GIT_SORT_REVERSE):
            commit_count += 1
            authors[commit.author.name] = authors.get(commit.author.name, 0) + 1
            if commit.oid in commit_tag.keys():
                tagname = commit_tag[commit.oid]
                result[tagname]['commits'] = commit_count
                result[tagname]['authors'] = authors

                commit_count = 0
                authors = {}

        return result
