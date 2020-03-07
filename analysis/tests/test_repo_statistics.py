import unittest
from unittest.mock import patch, MagicMock

from analysis.gitdata import WholeHistory
from analysis.gitrepository import GitRepository


class RepoStatisticsTest(unittest.TestCase):
    test_whole_history_records = [
        {'commit_sha': '6c40597', 'author_timestamp': 1580666336},
        {'commit_sha': '358604e', 'author_timestamp': 1583449674},
        {'commit_sha': 'fdc28ab', 'author_timestamp': 1185807283}
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
