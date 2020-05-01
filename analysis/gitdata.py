import abc
import pandas as pd
import pygit2 as git


class History(abc.ABC):

    def __init__(self, repository: git.Repository, branch: str = "master"):
        self.repo = repository
        self.branch = branch
        self.cache = None
        self.mailmap = git.Mailmap.from_repository(self.repo)

    def map_signature(self, signature: git.Signature):
        # the unmapped email is used on purpose
        email = signature.email
        try:
            mapped_signature = self.mailmap.resolve_signature(signature)
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
            author_name, author_email = self.map_signature(commit.author)

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
