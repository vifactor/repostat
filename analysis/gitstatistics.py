import pygit2 as git
from datetime import datetime
import warnings
import os

from tools.timeit import Timeit


class GitStatistics:
    def __init__(self, path, fetch_tags=True):
        """
        :param path: path to a repository
        """
        self.repo = git.Repository(path)
        self.mailmap = git.Mailmap.from_repository(self.repo)

        self.repo_name = os.path.basename(os.path.abspath(path))
        self.analysed_branch = self.repo.head.shorthand

        if fetch_tags:
            self.tags = self.fetch_tags_info()
        else:
            self.tags = {}

    def map_signature(self, sig: git.Signature) -> git.Signature:
        """
        Maps of a contributor signature as read from a repository using a provided .mailmap file
        :param sig: Signature to map
        :return: mapped signature
        """
        try:
            mapped_signature = self.mailmap.resolve_signature(sig)
        except ValueError as e:
            name = sig.name
            email = sig.email
            if not name:
                name = "Empty Empty"
                warnings.warn(f"{str(e)}. Name will be replaced with '{name}'")
            if not email:
                email = "empty@empty.empty"
                warnings.warn(f"{str(e)}. Email will be replaced with '{email}'")
            return git.Signature(name, email, sig.time, sig.offset, 'utf-8')
        else:
            return mapped_signature

    @classmethod
    def get_fetching_tool_info(cls):
        # could be bare git-subprocess invokation, PythonGit package, etc.
        return '{} v.{}'.format(git.__name__, git.LIBGIT2_VERSION)

    @Timeit("Fetching tags info")
    def fetch_tags_info(self):
        tags = [refobj for refobj in self.repo.listall_reference_objects() if refobj.name.startswith('refs/tags')]
        commit_tag = {refobj.peel().oid: refobj.shorthand for refobj in tags}

        result = {refobj.shorthand: {
            'stamp': refobj.peel().author.time,
            'date': datetime.fromtimestamp(refobj.peel().author.time).strftime('%Y-%m-%d'),
            'hash': str(refobj.target)} for refobj in tags}

        authors = {}
        commit_count = 0
        for commit in self.repo.walk(self.repo.head.target, git.GIT_SORT_TOPOLOGICAL | git.GIT_SORT_REVERSE):
            commit_count += 1
            commit_author = self.map_signature(commit.author)
            authors[commit_author.name] = authors.get(commit_author.name, 0) + 1
            if commit.oid in commit_tag.keys():
                tagname = commit_tag[commit.oid]
                result[tagname]['commits'] = commit_count
                result[tagname]['authors'] = authors

                commit_count = 0
                authors = {}

        return result
