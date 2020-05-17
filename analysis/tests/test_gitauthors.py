import unittest
from unittest.mock import patch, MagicMock

import datetime
import pytz
from pandas import DataFrame

from analysis.gitdata import WholeHistory
from analysis.gitrepository import GitRepository


class GitAuthorsTest(unittest.TestCase):
    test_whole_history_records = [
        {'commit_sha': '6c40597', 'author_name': 'Author1', 'author_tz_offset': 60, 'author_timestamp': 1580666336,
         'insertions': 4, 'deletions': 1, 'is_merge_commit': True, 'author_email': 'author1@domain.com'
         },
        {'commit_sha': '6c50597', 'author_name': 'Author2', 'author_tz_offset': 60, 'author_timestamp': 1580666146,
         'insertions': 3, 'deletions': 2, 'is_merge_commit': False, 'author_email': 'author2@domain.com'
         },
        {'commit_sha': '358604e', 'author_name': 'Author1', 'author_tz_offset': -120, 'author_timestamp': 1583449674,
         'insertions': 2, 'deletions': 3, 'is_merge_commit': False, 'author_email': 'author1@domain.com'
         },
        {'commit_sha': 'fdc28ab', 'author_name': 'Author3', 'author_tz_offset': 0, 'author_timestamp': 1185807283,
         'insertions': 1, 'deletions': 4, 'is_merge_commit': False, 'author_email': 'author3@domain.com'
         }
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

    @staticmethod
    def equals_authors_summary(author: str, summary: DataFrame, expected: dict):
        summary_columns = list(summary.columns.values)
        # remove 'authors_name' column
        summary_columns.remove('author_name')

        expected_summary_columns = list(expected.keys())
        # sort before checking for list equality
        summary_columns.sort()
        expected_summary_columns.sort()
        are_all_columns_checked = (summary_columns == expected_summary_columns)

        author_summary = summary.loc[summary['author_name'] == author].reset_index()
        all_entries_equal = all(v == author_summary[k][0] for k, v in expected.items())
        return are_all_columns_checked and all_entries_equal

    def get_first_commit_date(self, author):
        timestamps = [datetime.datetime.utcfromtimestamp(rec['author_timestamp'])
                      for rec in self.test_whole_history_records if rec['author_name'] == author]

        return min(timestamps).replace(tzinfo=pytz.utc)

    def get_latest_commit_date(self, author):
        timestamps = [datetime.datetime.utcfromtimestamp(rec['author_timestamp'])
                      for rec in self.test_whole_history_records if rec['author_name'] == author]

        return max(timestamps).replace(tzinfo=pytz.utc)

    def get_contributed_days_count(self, author):
        d2 = self.get_latest_commit_date(author)
        d1 = self.get_first_commit_date(author)
        days = (d2 - d1).days
        return days if days else 1

    def test_summary(self):
        summary = self.repo.authors.sort(by='deletions').summary
        self.assertTrue(self.equals_authors_summary('Author1', summary, {
            'contributed_days_count': self.get_contributed_days_count('Author1'),
            'active_days_count': 2,
            'first_commit_date': self.get_first_commit_date('Author1'),
            'latest_commit_date': self.get_latest_commit_date('Author1'),
            'insertions': 6,
            'deletions': 4,
            'merge_commits_count': 1,
            'commits_count': 2,
        }))

        self.assertTrue(self.equals_authors_summary('Author3', summary, {
            'contributed_days_count': self.get_contributed_days_count('Author3'),
            'active_days_count': 1,
            'first_commit_date': self.get_first_commit_date('Author3'),
            'latest_commit_date': self.get_latest_commit_date('Author3'),
            'insertions': 1,
            'deletions': 4,
            'merge_commits_count': 0,
            'commits_count': 1,
        }))

    def test_history(self):
        # TODO: figure out how to test it properly
        print(self.repo.authors.history('W')['insertions'])


