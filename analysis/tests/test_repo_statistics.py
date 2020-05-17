import unittest
from unittest.mock import patch, MagicMock

from datetime import datetime

from analysis.gitdata import WholeHistory
from analysis.gitrepository import GitRepository
from analysis.gitauthor import GitAuthor


def to_unix_time(dt: datetime):
    epoch = datetime.utcfromtimestamp(0)
    return (dt - epoch).total_seconds()


class RepoStatisticsTest(unittest.TestCase):
    test_whole_history_records = [
        {'commit_sha': '6c40597', 'author_name': 'Author1', 'author_email': 'author1@author1.com',
         'author_tz_offset': 60, 'author_timestamp': 1580666336,
         'insertions': 1, 'deletions': 0},
        {'commit_sha': '6c50597', 'author_name': 'Author2', 'author_email': 'author2@author2.com',
         'author_tz_offset': 60, 'author_timestamp': 1580666146,
         'insertions': 1, 'deletions': 0},
        {'commit_sha': '358604e', 'author_name': 'Author1', 'author_email': 'author1@author1.com',
         'author_tz_offset': -120, 'author_timestamp': 1583449674,
         'insertions': 1, 'deletions': 0},
        {'commit_sha': 'fdc28ab', 'author_name': 'Author3', 'author_email': 'author3@author3.com',
         'author_tz_offset': 0, 'author_timestamp': 1185807283,
         'insertions': 1, 'deletions': 0}
    ]

    @classmethod
    def setUpClass(cls):
        GitAuthor.author_groups = None

    @patch.object(WholeHistory, 'fetch', return_value=test_whole_history_records)
    def test_whole_history_fetched(self, mock_fetch):
        with patch("pygit2.Mailmap"):
            df = WholeHistory(MagicMock()).as_dataframe()
            mock_fetch.assert_called()
            self.assertEqual(len(self.test_whole_history_records), len(df.index))

    @patch.object(WholeHistory, 'fetch', return_value=test_whole_history_records)
    def test_whole_history_once_for_statistics(self, mock_fetch):
        with patch("pygit2.Repository"),\
                patch("pygit2.Mailmap"):
            GitRepository(MagicMock())
            self.assertEqual(1, mock_fetch.call_count)

    @patch.object(WholeHistory, 'fetch', return_value=test_whole_history_records)
    def test_first_last_timestamps(self, mock_fetch):
        with patch("pygit2.Repository"),\
                patch("pygit2.Mailmap"):
            timestamps = [rec['author_timestamp'] for rec in self.test_whole_history_records]
            expected_last_commit_timestamp = max(timestamps)
            expected_first_commit_timestamp = min(timestamps)

            stat = GitRepository(MagicMock())
            self.assertEqual(expected_first_commit_timestamp, stat.first_commit_timestamp)
            self.assertEqual(expected_last_commit_timestamp, stat.last_commit_timestamp)

    @patch.object(WholeHistory, 'fetch', return_value=test_whole_history_records)
    def test_active_days_count(self, mock_fetch):
        with patch("pygit2.Repository"),\
                patch("pygit2.Mailmap"):
            expected_active_days = {datetime.fromtimestamp(rec['author_timestamp']).strftime('%Y-%m-%d') for rec in
                                    self.test_whole_history_records}
            stat = GitRepository(MagicMock())
            self.assertEqual(len(expected_active_days), stat.active_days_count)

    def get_expected_timezones_dict(self):
        import pytz
        from collections import Counter

        # this calculation repeats the one present in analysis/gitrepository.py not using pandas
        tzs = {datetime.utcnow().astimezone(tz=pytz.FixedOffset(rec['author_tz_offset'])) for rec in
               self.test_whole_history_records}

        tzs_count = Counter(tz.strftime('%z') for tz in tzs)

        return dict(tzs_count)

    @patch.object(WholeHistory, 'fetch', return_value=test_whole_history_records)
    def test_timezones_distribution(self, mock_fetch):
        with patch("pygit2.Repository"),\
                patch("pygit2.Mailmap"):
            stat = GitRepository(MagicMock())
            expected_timezones = self.get_expected_timezones_dict()
            self.assertDictEqual(expected_timezones, stat.timezones_distribution)

    @patch.object(WholeHistory, 'fetch', return_value=test_whole_history_records)
    def test_domains_distribution(self, mock_fetch):
        with patch("pygit2.Repository"), patch("pygit2.Mailmap"):
            stat = GitRepository(MagicMock())

            expected_domains = {'author1.com': 2, 'author2.com': 1, 'author3.com': 1}
            self.assertDictEqual(expected_domains, stat.domains_distribution.to_dict())

    @patch.object(WholeHistory, 'fetch', return_value=[
        {'commit_sha': 'fdc28ab', 'author_name': '', 'author_tz_offset': 0,
         'author_timestamp': to_unix_time(datetime.utcnow()), 'author_email': 'author1@author1.com'}
    ])
    def test_recent_activity(self, mock_fetch):
        with patch("pygit2.Repository"),\
                patch("pygit2.Mailmap"):
            stat = GitRepository(MagicMock())
            two_weeks_activity = stat.get_recent_weekly_activity(2)
            self.assertListEqual([0, 1], list(two_weeks_activity))

    @patch.object(WholeHistory, 'fetch', return_value=[
        {'commit_sha': 'aaaaaaa', 'author_name': 'Author1', 'author_tz_offset': 60,
         'author_timestamp': to_unix_time(datetime(2020, 1, 17)), 'author_email': 'author1@domain.com'},
        {'commit_sha': 'bbbbbbb', 'author_name': 'Author2', 'author_tz_offset': 60,
         'author_timestamp': to_unix_time(datetime(2019, 11, 15)), 'author_email': 'author2@domain.com'},
        {'commit_sha': 'ccccccc', 'author_name': 'Author1', 'author_tz_offset': -120,
         'author_timestamp': to_unix_time(datetime(2020, 3, 1)), 'author_email': 'author1@domain.com'},
    ])
    def test_authors_top(self, mock_fetch):
        with patch("pygit2.Repository"),\
                patch("pygit2.Mailmap"):
            stat = GitRepository(MagicMock())

            authors_ts = stat.get_authors_ranking_by_year()
            self.assertEqual(2, authors_ts.loc[(2020, 'Author1')])
            self.assertEqual(1, authors_ts.loc[(2019, 'Author2')])

            authors_ts = stat.get_authors_ranking_by_month()
            self.assertEqual(1, authors_ts.loc[('2020-03', 'Author1')])
            self.assertEqual(1, authors_ts.loc[('2019-11', 'Author2')])
