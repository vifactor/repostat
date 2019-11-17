import unittest

import datetime

from analysis import GitStatistics
import test


class TestSingleCommitRepository(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.git_repository = test.GitRepository()

        cls.git_repository.commit_builder\
            .set_author("John Doe", "john@doe.com")\
            .add_file()\
            .commit()

        cls.commit_author, = cls.git_repository.commit_builder.author_signatures
        cls.gs = GitStatistics(cls.git_repository.location)

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
