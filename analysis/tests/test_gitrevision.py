import unittest
from unittest.mock import patch, MagicMock

from analysis.gitdata import BlameData, FilesData
from analysis.gitrevision import GitRevision


class GitRevisionTest(unittest.TestCase):
    # "committer_name", "lines_count", "timestamp", "filepath"
    test_revision_blame_data_records = [
        ['Author1', 1, 1580666336, "file1.txt"],
        ['Author2', 2, 1580666146, "file2.txt"],
        ['Author1', 3, 1583449674, "file3.txt"],
        ['Author3', 4, 1185807283, "file1.txt"]
    ]

    test_revision_files_data_records = [
        {"file": 'file1.txt', "is_binary": False, "size_bytes": 1, "lines_count": 1},
        {"file": 'file2.dat', "is_binary": False, "size_bytes": 4, "lines_count": 2},
        {"file": 'folder/file3.log', "is_binary": False, "size_bytes": 8, "lines_count": 3},
        {"file": 'folder/file4.txt', "is_binary": False, "size_bytes": 16, "lines_count": 4}
    ]

    @patch.object(BlameData, 'fetch', return_value=test_revision_blame_data_records)
    def test_contribution(self, mock_fetch):
        with patch("pygit2.Mailmap"):
            revision = GitRevision(MagicMock())
            self.assertDictEqual(revision.authors_contribution.to_dict(),
                                 {'Author1': 4, 'Author3': 4, 'Author2': 2})

    @patch.object(FilesData, '_fetch', return_value=test_revision_files_data_records)
    def test_files_count(self, mock_fetch):
        with patch("pygit2.Mailmap"):
            revision = GitRevision(MagicMock())
            self.assertEqual(len(self.test_revision_files_data_records), revision.files_count)

    @patch.object(FilesData, '_fetch', return_value=test_revision_files_data_records)
    def test_files_extension_summary(self, mock_fetch):
        with patch("pygit2.Mailmap"):
            revision = GitRevision(MagicMock())
            self.assertDictEqual(revision.files_extensions_summary["lines_count"].to_dict(),
                                 {(False, 'dat'): 2, (False, 'log'): 3, (False, 'txt'): 5})
            self.assertDictEqual(revision.files_extensions_summary["files_count"].to_dict(),
                                 {(False, 'dat'): 1, (False, 'log'): 1, (False, 'txt'): 2})
