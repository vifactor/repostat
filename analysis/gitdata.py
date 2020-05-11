import abc
import os
import pandas as pd
import pygit2 as git
from concurrent.futures import ThreadPoolExecutor


def map_signature(mailmap, signature: git.Signature):
    # the unmapped email is used on purpose
    email = signature.email
    try:
        mapped_signature = mailmap.resolve_signature(signature)
        name = mapped_signature.name
    except ValueError:
        name = signature.name
        if not name:
            name = "Empty Empty"
            # warnings.warn(f"{str(e)}. Name will be replaced with '{name}'")
        if not email:
            email = "empty@empty.empty"
            # warnings.warn(f"{str(e)}. Email will be replaced with '{email}'")
    return name, email


class History(abc.ABC):

    def __init__(self, repository: git.Repository, branch: str = "master"):
        self.repo = repository
        self.branch = branch
        self.cache = None
        self.mailmap = git.Mailmap.from_repository(self.repo)

    def as_dataframe(self):
        data = self.fetch()
        return pd.DataFrame(data)

    @abc.abstractmethod
    def fetch(self):
        pass


class WholeHistory(History):
    def fetch(self):
        repo_walker = self.repo.walk(self.repo.head.target, git.GIT_SORT_TOPOLOGICAL)
        records = []
        for commit in repo_walker:
            author_name, author_email = map_signature(self.mailmap, commit.author)

            is_merge_commit = False
            insertions, deletions = 0, 0
            if len(commit.parents) == 0:  # initial commit
                st = commit.tree.diff_to_tree(swap=True).stats
                insertions, deletions = st.insertions, st.deletions
            elif len(commit.parents) == 1:
                parent_commit = commit.parents[0]
                st = self.repo.diff(parent_commit, commit).stats
                insertions, deletions = st.insertions, st.deletions
            # case len(commit.parents) > 1 corresponds to a merge commit
            # merge commits are ignored: changes in merge commits are normally because of integration issues
            else:
                is_merge_commit = True

            records.append({'commit_sha': commit.hex[:7],
                            'is_merge_commit': is_merge_commit,
                            'author_name': author_name,
                            'author_email': author_email,
                            'author_tz_offset': commit.author.offset,
                            'author_timestamp': commit.author.time,
                            'review_duration': commit.committer.time - commit.author.time,
                            'insertions': insertions,
                            'deletions': deletions})
        return records


class LinearHistory(History):
    def fetch(self):
        repo_walker = self.repo.walk(self.repo.head.target, git.GIT_SORT_TOPOLOGICAL)
        repo_walker.simplify_first_parent()
        records = []
        for commit in repo_walker:

            insertions, deletions = 0, 0
            if len(commit.parents) == 0:  # initial commit
                st = commit.tree.diff_to_tree(swap=True).stats
                insertions, deletions = st.insertions, st.deletions
            elif len(commit.parents) >= 1:
                parent_commit = commit.parents[0]
                st = self.repo.diff(parent_commit, commit).stats
                insertions, deletions = st.insertions, st.deletions

            records.append({'commit_sha': commit.hex[:7],
                            'committer_timestamp': commit.committer.time,
                            'files_count': len(commit.tree.diff_to_tree()),
                            'insertions': insertions,
                            'deletions': deletions})
        return records


class RevisionData:
    """
    Class to fetch raw data about repository state at certain revision
    """
    def __init__(self, repository: git.Repository, revision: str = None):
        self.repo = repository
        self.mailmap = git.Mailmap.from_repository(self.repo)
        self.revision_commit = self.repo.revparse_single(revision) if revision else self.repo.head.peel()

    def _get_data_from_blame_hunk(self, blame_hunk):
        hunk_committer = blame_hunk.final_committer
        if not hunk_committer:
            # if committer configured an empty email when created commit
            # blame hunk corresponding to that commit will produce a None signature
            # the following substitutes hunk's final committer with an author of the commit
            hunk_committer = self.repo[blame_hunk.orig_commit_id].author
        committer_name, _ = map_signature(self.mailmap, hunk_committer)
        return [committer_name, blame_hunk.lines_in_hunk, hunk_committer.time]

    def blame_file(self, file_path):
        blob_blame = self.repo.blame(file_path)
        blame_info = [self._get_data_from_blame_hunk(blame_hunk) + [file_path] for blame_hunk in blob_blame]
        return blame_info

    def fetch(self):
        submodules_paths = self.repo.listall_submodules()
        diff_to_tree = self.revision_commit.tree.diff_to_tree()
        files_to_blame = (p.delta.new_file.path for p in diff_to_tree
                          if not p.delta.is_binary and p.delta.new_file.path not in submodules_paths)

        # this number of workers gets assigned in Python 3.8 if "max_workers"-argument of ThreadPoolExecutor is None
        # see https://docs.python.org/3/library/concurrent.futures.html#concurrent.futures.ThreadPoolExecutor
        workers_count = min(32, os.cpu_count() + 4)
        # checks revealed that the task is rather "IO-bound", i.e. using ProcessPoolExecutor is not necessary
        # while Processes Pool gives comparable performance boost, it make program structure a bit more complicated
        with ThreadPoolExecutor(max_workers=workers_count) as pool:
            results = pool.map(self.blame_file, files_to_blame)
        return [rec for val in results for rec in val]

    def as_dataframe(self):
        data = self.fetch()
        return pd.DataFrame(data, columns=["committer_name", "lines_count", "timestamp", "filepath"])
