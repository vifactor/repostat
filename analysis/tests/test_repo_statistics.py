import unittest
from unittest.mock import patch, MagicMock
from analysis.gitdata import WholeHistory


class RepoStatisticsTest(unittest.TestCase):
    test_whole_history_records = [
        [1],
    ]

    @patch.object(WholeHistory, 'fetch', return_value=test_whole_history_records)
    def test_raw_data_fetched(self, mock_fetch):
        df = WholeHistory(MagicMock()).as_dataframe()
        mock_fetch.assert_called()
        self.assertEqual(len(self.test_whole_history_records), df.size)
