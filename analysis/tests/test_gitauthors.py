import unittest
from unittest.mock import patch, MagicMock

from pandas import DataFrame

from analysis.gitdata import WholeHistory
from analysis.gitrepository import GitRepository


class GitAuthorsTest(unittest.TestCase):
    test_whole_history_records = [
        {'commit_sha': '6c40597', 'author_name': 'Author1', 'author_tz_offset': 60, 'author_timestamp': 1580666336,
         'insertions': 4, 'deletions': 1
         },
        {'commit_sha': '6c50597', 'author_name': 'Author2', 'author_tz_offset': 60, 'author_timestamp': 1580666146,
         'insertions': 3, 'deletions': 2
         },
        {'commit_sha': '358604e', 'author_name': 'Author1', 'author_tz_offset': -120, 'author_timestamp': 1583449674,
         'insertions': 2, 'deletions': 3},
        {'commit_sha': 'fdc28ab', 'author_name': 'Author3', 'author_tz_offset': 0, 'author_timestamp': 1185807283,
         'insertions': 1, 'deletions': 4}
    ]

    @classmethod
    def setUp(cls):
        with patch("pygit2.Mailmap"), \
             patch("pygit2.Repository"), \
             patch.object(WholeHistory, 'fetch', return_value=cls.test_whole_history_records):
            cls.repo = GitRepository(MagicMock())

    def test_authors_count(self):
        self.assertEqual(3, self.repo.authors.count())

    def test_authors_names(self):
        # arbitrary sorting
        self.assertCountEqual(['Author2', 'Author1', 'Author3'], list(self.repo.authors.names()))

    def test_sort_by_commits_count(self):
        names_sorted_by_commits_count = self.repo.authors.sort().names()
        # first author has 2 commits
        self.assertEqual('Author1', names_sorted_by_commits_count[0])
        # second and third authors have both by 1 commits
        self.assertCountEqual(['Author3', 'Author2'], names_sorted_by_commits_count[1:])

    def test_summary(self):
        summary = self.repo.authors.sort(by='deletions').summary

        author1_summary = summary.loc[summary['author_name'] == 'Author1']
        expected_author1_summary = DataFrame([{'author_name': 'Author1',
                                               'insertions': 6,
                                               'deletions': 4,
                                               'commits_count': 2}])
        self.assertTrue(author1_summary.equals(expected_author1_summary))

        author3_summary = summary.loc[summary['author_name'] == 'Author3'].reset_index(drop=True)
        expected_author3_summary = DataFrame([{'author_name': 'Author3',
                                               'insertions': 1,
                                               'deletions': 4,
                                               'commits_count': 1}])
        self.assertTrue(author3_summary.equals(expected_author3_summary))

    def test_history(self):
        # TODO: figure out how to test it properly
        print(self.repo.authors.history('W')['insertions'])


