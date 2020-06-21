import abc
import pandas as pd
import pygit2 as git

from tqdm import tqdm
from tqdm.contrib.concurrent import thread_map

from tools.timeit import Timeit


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
        df = pd.DataFrame(data)
        return self._optimize(df)

    @abc.abstractmethod
    def fetch(self):
        pass

    @abc.abstractmethod
    def _optimize(self, df: pd.DataFrame):
        return df

    @property
    def commits_walker(self):
        return self.repo.walk(self.repo.head.target, git.GIT_SORT_TOPOLOGICAL)

    def get_commits_count(self):
        return sum(1 for _ in self.commits_walker)


class WholeHistory(History):

    @Timeit("Fetching whole history data")
    def fetch(self):
        records = []
        for commit in tqdm(self.commits_walker, total=self.get_commits_count()):
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

    def _optimize(self, df: pd.DataFrame):
        df['author_name'] = pd.Categorical(df['author_name'])
        df['author_email'] = pd.Categorical(df['author_email'])
        return df


class LinearHistory(History):

    @Timeit("Fetching linear history data")
    def fetch(self):
        records = []
        for commit in tqdm(self.commits_walker, total=self.get_commits_count()):

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

    def _optimize(self, df: pd.DataFrame):
        return super()._optimize(df)

    @property
    def commits_walker(self):
        walker = super(LinearHistory, self).commits_walker
        walker.simplify_first_parent()
        return walker


class BlameData:
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

    @Timeit("Fetching blame data")
    def fetch(self):
        submodules_paths = self.repo.listall_submodules()
        diff_to_tree = self.revision_commit.tree.diff_to_tree()
        files_to_blame = [p.delta.new_file.path for p in diff_to_tree
                          if not p.delta.is_binary and p.delta.new_file.path not in submodules_paths]

        results = thread_map(self.blame_file, files_to_blame)
        return [rec for val in results for rec in val]

    def as_dataframe(self):
        data = self.fetch()
        df = pd.DataFrame(data, columns=["committer_name", "lines_count", "timestamp", "filepath"])
        # this saves some memory
        df["committer_name"] = pd.Categorical(df["committer_name"])
        df["filepath"] = pd.Categorical(df["filepath"])
        return df


class FilesData:
    """
    Class to fetch raw data about repository state at certain revision
    """
    def __init__(self, repository: git.Repository, revision: str = None):
        self.repo = repository
        self.revision_commit = self.repo.revparse_single(revision) if revision else self.repo.head.peel()

    @Timeit("Fetching files data")
    def _fetch(self):
        submodules_paths = self.repo.listall_submodules()
        head_commit_tree = self.revision_commit.tree.diff_to_tree(swap=True)
        records = []
        for p in head_commit_tree:
            filepath = p.delta.new_file.path
            if filepath not in submodules_paths:
                records.append({
                    "file": filepath,
                    "is_binary": p.delta.is_binary,
                    "size_bytes": p.delta.new_file.size,
                    "lines_count": p.line_stats[1]
                })
        return records

    def as_dataframe(self):
        data = self._fetch()
        df = pd.DataFrame(data)
        return df


class TagsData:
    def __init__(self, repository: git.Repository):
        """
        :param path: path to a repository
        """
        self.repo = repository
        self.mailmap = git.Mailmap.from_repository(self.repo)

    @Timeit("Fetching tags info")
    def fetch(self):
        # TODO: this should perhaps be a part of WholeHistory
        tag_refs = {refobj.peel().oid: refobj
                    for refobj in self.repo.listall_reference_objects() if refobj.name.startswith('refs/tags')}

        result = []
        tag_ref = None
        is_symbolic_reference = False
        for commit in self.repo.walk(self.repo.head.target, git.GIT_SORT_TOPOLOGICAL):
            author_name, _ = map_signature(self.mailmap, commit.author)
            if commit.oid in tag_refs:
                tag_ref: git.Reference = tag_refs[commit.oid]
                is_symbolic_reference = tag_ref.target.hex == commit.hex

            if tag_ref is not None:
                if not is_symbolic_reference:
                    tag = self.repo[tag_ref.target]
                    tagger_name, _ = map_signature(self.mailmap, tag.tagger)
                    tag_metadata = {
                        "tag_name": tag.name,
                        "tagger_name": tagger_name,
                        "tagger_time": tag.tagger.time,
                    }
                else:
                    tag_metadata = {
                        "tag_name": tag_ref.shorthand,
                        "tagger_name": None,
                        "tagger_time": -1,
                    }
            else:
                tag_metadata = {
                    "tag_name": None,
                    "tagger_name": None,
                    "tagger_time": -1,
                }
            tag_metadata["commit_author"] = author_name
            tag_metadata["commit_time"] = commit.author.time
            tag_metadata["is_merge"] = len(commit.parents) > 1
            result.append(tag_metadata)

        return result

    def as_dataframe(self):
        raw_data = pd.DataFrame(self.fetch())
        # TODO: optimize memory by changing some datatypes
        # .astype('bool')
        return raw_data
