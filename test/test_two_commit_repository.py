import unittest

import os

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

    @unittest.skipIf(not GitStatistics.is_mailmap_supported, "Mailmap is not supported")
    def test_mailmap(self):
        commit_author1, commit_author2 = self.git_repository.commit_builder.author_signatures
        with open(os.path.join(self.git_repository.location, ".mailmap"), 'w') as mm:
            mm.write(f"{commit_author1.name} <{commit_author1.email}> "
                     f"{commit_author2.name} <{commit_author2.email}>")

        gs = GitStatistics(self.git_repository.location)

        # only one author in authors
        self.assertListEqual([commit_author1.name], list(gs.authors.keys()))
        # but he/she has 2 commits
        self.assertEqual(2, gs.authors[commit_author1.name]['commits'])

        # in history only 1st author is present
        # TODO: add relevant check
        #authors_in_history = {author for val in gs.author_changes_history.values() for author in val.keys()}
        #self.assertSetEqual({commit_author1.name}, authors_in_history)

    def test_contributors(self):
        gs = GitStatistics(self.git_repository.location)
        contributors = gs.fetch_contributors()
        # TODO: make commit builder remember the number of added lines and use info here
        self.assertDictEqual({'John Doe II': 2, 'John Doe I': 1}, contributors)
