import unittest
from unittest.mock import patch, MagicMock

from datetime import datetime

from analysis.gitdata import WholeHistory
from analysis.gitrepository import GitRepository


def to_unix_time(dt: datetime):
    epoch = datetime.utcfromtimestamp(0)
    return (dt - epoch).total_seconds()


class AuthorStatisticsTest(unittest.TestCase):
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
    def setUpClass(cls):
        with patch("pygit2.Mailmap"), \
             patch("pygit2.Repository"), \
             patch.object(WholeHistory, 'fetch', return_value=cls.test_whole_history_records):
            cls.repo_stat = GitRepository(MagicMock())

    def test_author_properties(self):
        author_stat = self.repo_stat.get_author('Author1')

        self.assertEqual(2, author_stat.active_days_count)
        self.assertEqual(2, author_stat.commits_count)
        self.assertEqual(datetime.utcfromtimestamp(1583449674), author_stat.latest_commit_date)
        self.assertEqual(datetime.utcfromtimestamp(1580666336), author_stat.first_commit_date)

        self.assertEqual(6, author_stat.lines_added)
        self.assertEqual(4, author_stat.lines_removed)
