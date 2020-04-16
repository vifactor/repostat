import unittest

from analysis import GitStatistics
import test


class TestTwoCommitRepository(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.git_repository = test.GitRepository()

        cls.git_repository.commit_builder\
            .set_author("John Doe I", "john1@doe.com")\
            .add_file(content=["Line by John Doe I"])\
            .commit()

        cls.git_repository.commit_builder\
            .set_author("John Doe II", "john2@doe.com")\
            .add_file(content=["Line 1 by John Doe II", "Line 2 by John Doe II"])\
            .commit()

    def test_contributors(self):
        gs = GitStatistics(self.git_repository.location)
        contributors = gs.fetch_contributors()
        # TODO: make commit builder remember the number of added lines and use info here
        self.assertDictEqual({'John Doe II': 2, 'John Doe I': 1}, contributors)
