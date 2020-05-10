import unittest
from unittest.mock import patch, MagicMock

from analysis.gitdata import RevisionData
from analysis.gitrevision import GitRevision


class GitRevisionTest(unittest.TestCase):
    # "committer_name", "lines_count", "timestamp", "filepath"
    test_revision_data_records = [
        ['Author1', 1, 1580666336, "file1.txt"],
        ['Author2', 2, 1580666146, "file2.txt"],
        ['Author1', 3, 1583449674, "file3.txt"],
        ['Author3', 4, 1185807283, "file1.txt"]
    ]

    @patch.object(RevisionData, 'fetch', return_value=test_revision_data_records)
    def test_contribution(self, mock_fetch):
        with patch("pygit2.Mailmap"):
            revision = GitRevision(RevisionData(MagicMock()))
            self.assertDictEqual(revision.authors_contribution.to_dict(),
                                 {'Author1': 4, 'Author3': 4, 'Author2': 2})
