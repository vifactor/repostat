import pygit2 as git
import tempfile
import shutil
import os

from typing import List


class GitTestRepository(git.Repository):
    class CommitBuilder:

        def __init__(self, repo):
            self.repository = repo
            self.author_signature = None
            self.commits_count = 0
            self.latest_commit = None
            self.author_signatures = []

        def add_file(self, filename=None, content: List[str] = None):
            if filename is None:
                (fd, file_abs_path) = tempfile.mkstemp(dir=self.repository.location)
                file_rel_path = os.path.basename(file_abs_path)
                os.close(fd)
            else:
                file_rel_path = filename

            if content is not None:
                with open(os.path.join(self.repository.location, file_rel_path), 'w') as f:
                    for line in content:
                        f.write(line + "\n")

            self.repository.index.add(file_rel_path)
            self.repository.index.write()
            return self

        def append_file(self, filename, content: List[str]):
            with open(os.path.join(self.repository.location, filename), 'a+') as f:
                for line in content:
                    f.write(f"{line}\n")

            self.repository.index.add(filename)
            self.repository.index.write()
            return self

        def set_author(self, name: str, email: str):
            self.author_signature = git.Signature(name, email)
            return self

        def commit(self):
            tree = self.repository.index.write_tree()
            committer = self.author_signature
            commit_message = f"Commit number {self.commits_count}"
            parents = [self.repository.head.peel().oid] if self.latest_commit is not None else []
            commit_oid = self.repository.create_commit('HEAD',
                                                       self.author_signature, committer,
                                                       commit_message, tree, parents)
            self.commits_count += 1
            self.latest_commit = commit_oid
            self.author_signatures.append(self.author_signature)
            self.author_signature = None
            return commit_oid

    def __init__(self, loc=None, clean=True):
        self.clean = clean
        self.location = loc if loc is not None else tempfile.mkdtemp(prefix="repostat_")
        git.init_repository(self.location)
        super().__init__(self.location)
        print(f"Repo has been initialized in {self.location}")
        self.commit_builder = GitTestRepository.CommitBuilder(self)

    def __del__(self):
        if self.clean:
            shutil.rmtree(self.location)
            print(f"Repo has been removed from {self.location}")
