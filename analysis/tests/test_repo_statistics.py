import unittest
from unittest.mock import patch, MagicMock

from datetime import datetime

from analysis.gitdata import WholeHistory
from analysis.gitrepository import GitRepository


class RepoStatisticsTest(unittest.TestCase):
    test_whole_history_records = [
        {'commit_sha': '6c40597', 'author_tz_offset': 60, 'author_timestamp': 1580666336},
        {'commit_sha': '6c50597', 'author_tz_offset': 60, 'author_timestamp': 1580666146},
        {'commit_sha': '358604e', 'author_tz_offset': -120, 'author_timestamp': 1583449674},
        {'commit_sha': 'fdc28ab', 'author_tz_offset': 0, 'author_timestamp': 1185807283}
    ]

    @patch.object(WholeHistory, 'fetch', return_value=test_whole_history_records)
    def test_whole_history_fetched(self, mock_fetch):
        df = WholeHistory(MagicMock()).as_dataframe()
        mock_fetch.assert_called()
        self.assertEqual(len(self.test_whole_history_records), len(df.index))

    @patch.object(WholeHistory, 'fetch', return_value=test_whole_history_records)
    def test_whole_history_once_for_statistics(self, mock_fetch):
        with patch("pygit2.Repository"):
            GitRepository(MagicMock())
            self.assertEqual(1, mock_fetch.call_count)

    @patch.object(WholeHistory, 'fetch', return_value=test_whole_history_records)
    def test_first_last_timestamps(self, mock_fetch):
        with patch("pygit2.Repository"):
            timestamps = [rec['author_timestamp'] for rec in self.test_whole_history_records]
            expected_last_commit_timestamp = max(timestamps)
            expected_first_commit_timestamp = min(timestamps)

            stat = GitRepository(MagicMock())
            self.assertEqual(expected_first_commit_timestamp, stat.first_commit_timestamp)
            self.assertEqual(expected_last_commit_timestamp, stat.last_commit_timestamp)

    @patch.object(WholeHistory, 'fetch', return_value=test_whole_history_records)
    def test_active_days_count(self, mock_fetch):
        with patch("pygit2.Repository"):
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
        with patch("pygit2.Repository"):
            stat = GitRepository(MagicMock())
            expected_timezones = self.get_expected_timezones_dict()
            self.assertDictEqual(expected_timezones, stat.timezones_distribution)
