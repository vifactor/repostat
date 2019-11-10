import unittest

import tempfile
import os
import pygit2 as git
import datetime

from analysis import GitStatistics


class TestSingleCommitRepository(unittest.TestCase):
    git_repository_dir = None

    @classmethod
    def setUpClass(cls):
        cls.git_repository_dir = tempfile.mkdtemp(prefix="repostat_")
        print(f"Repo is going to be initialized in {cls.git_repository_dir}")
        cls.git_repository = git.init_repository(cls.git_repository_dir)
        (_, file_abs_path) = tempfile.mkstemp(dir=cls.git_repository_dir)
        file_rel_path = os.path.basename(file_abs_path)

        cls.git_repository.index.add(file_rel_path)
        cls.git_repository.index.write()
        tree = cls.git_repository.index.write_tree()

        cls.commit_author = git.Signature("John Doe", "john@doe.com")
        committer = cls.commit_author
        commit_message = "First commit"
        commit_oid = cls.git_repository.create_commit('HEAD', cls.commit_author, committer, commit_message, tree, [])
        print(f"Commit {commit_oid.hex[:7]} has been created")

        cls.gs = GitStatistics(cls.git_repository_dir)

    @classmethod
    def tearDownClass(cls):
        print(f"Repo {cls.git_repository_dir} is being deleted")

    def test_total_commits_number(self):
        self.assertEqual(self.gs.total_commits, 1)

    def test_authors_statistics(self):
        self.assertIn(self.commit_author.name, self.gs.authors)

        author_stats = self.gs.authors[self.commit_author.name]
        self.assertEqual(author_stats['lines_added'], 0)
        self.assertEqual(author_stats['lines_removed'], 0)
        self.assertEqual(len(author_stats['active_days']), 1)
        self.assertEqual(author_stats['commits'], 1)
        self.assertEqual(author_stats['place_by_commits'], 1)

        today = str(datetime.datetime.today().date())
        self.assertEqual(author_stats['date_first'], today)
        self.assertEqual(author_stats['date_last'], today)
        # total activity days count is not checked


if __name__ == '__main__':
    unittest.main()
