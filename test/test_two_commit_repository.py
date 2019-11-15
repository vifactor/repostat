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
            .add_file(content=["Line by John Doe II"])\
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

        # single domain is in the list (corresponds to email of the 1st author)
        self.assertEqual(1, len(gs.domains))

        # in history only 1st author is present
        authors_in_history = {author for val in gs.author_changes_history.values() for author in val.keys()}
        self.assertSetEqual({commit_author1.name}, authors_in_history)

        # author of the year are estimated similarly so only author of the month is checked
        nominated_authors = {author for val in gs.author_of_month.values() for author in val.keys()}
        self.assertSetEqual({commit_author1.name}, nominated_authors)
