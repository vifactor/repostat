import unittest
from unittest.mock import patch, MagicMock

import datetime

from analysis.gitdata import TagsData
from analysis.gittags import GitTags


class GitTagsTest(unittest.TestCase):
    test_tags_data_records = [
        {"tag_name": None, "tagger_name": None, "tagger_time": -1, "commit_author": "Committer1",
         "commit_time": 1230000, "is_merge": False},
        {"tag_name": "v2", "tagger_name": "Release Master", "tagger_time": 1234, "commit_author": "Author2",
         "commit_time": 123000, "is_merge": True},
        {"tag_name": "v2", "tagger_name": "Release Master", "tagger_time": 1234, "commit_author": "Author1",
         "commit_time": 123, "is_merge": False},
        {"tag_name": "v2", "tagger_name": "Release Master", "tagger_time": 1234, "commit_author": "Author1",
         "commit_time": 14, "is_merge": False}
    ]

    @patch.object(TagsData, 'fetch', return_value=test_tags_data_records)
    def test_tags_all(self, mock_fetch):
        with patch("pygit2.Mailmap"):
            tags = GitTags(MagicMock()).all()
            self.assertEqual(2, len(list(tags)))

    @patch.object(TagsData, 'fetch', return_value=test_tags_data_records)
    def test_tag_commits_count(self, mock_fetch):
        with patch("pygit2.Mailmap"):
            v2_tag = GitTags(MagicMock()).get('v2')
            self.assertEqual(3, v2_tag.commits_count)

    @patch.object(TagsData, 'fetch', return_value=test_tags_data_records)
    def test_tag_contributors(self, mock_fetch):
        with patch("pygit2.Mailmap"):
            v2_tag = GitTags(MagicMock()).get('v2')
            self.assertDictEqual({'Author1': 2, 'Author2': 1}, v2_tag.contributors['commits_count'].to_dict())

    @patch.object(TagsData, 'fetch', return_value=test_tags_data_records)
    def test_tag_contributors(self, mock_fetch):
        with patch("pygit2.Mailmap"):
            v2_tag = GitTags(MagicMock()).get('v2')
            self.assertDictEqual({'Author1': 2, 'Author2': 1}, v2_tag.contributors['commits_count'].to_dict())

    @patch.object(TagsData, 'fetch', return_value=test_tags_data_records)
    def test_tag_timings(self, mock_fetch):
        with patch("pygit2.Mailmap"):
            v2_tag = GitTags(MagicMock()).get('v2')
            self.assertEqual(datetime.datetime.utcfromtimestamp(1234).replace(tzinfo=datetime.timezone.utc),
                             v2_tag.created)
            self.assertEqual(datetime.datetime.utcfromtimestamp(14).replace(tzinfo=datetime.timezone.utc),
                             v2_tag.initiated)

    @patch.object(TagsData, 'fetch', return_value=test_tags_data_records)
    def test_unreleased_tag_accessible(self, mock_fetch):
        with patch("pygit2.Mailmap"):
            tags = GitTags(MagicMock()).all()
            unreleased_tag = next(tags)
            self.assertEqual('unreleased', str(unreleased_tag))

    @patch.object(TagsData, 'fetch', return_value=test_tags_data_records)
    def test_tag_tagger(self, mock_fetch):
        with patch("pygit2.Mailmap"):
            tags = GitTags(MagicMock()).all()
            unreleased_tag = next(tags)
            self.assertIsNone(unreleased_tag.tagger)

            v2_tag = next(tags)
            self.assertEqual("Release Master", v2_tag.tagger)

    @patch.object(TagsData, 'fetch', return_value=[
        {"tag_name": None, "tagger_name": None, "tagger_time": -1, "commit_author": "Committer1",
         "commit_time": 1230000, "is_merge": False},
        {"tag_name": None, "tagger_name": None, "tagger_time": -1, "commit_author": "Author2",
         "commit_time": 123000, "is_merge": True}])
    def test_repo_with_no_tags(self, mock_fetch):
        with patch("pygit2.Mailmap"):
            tags = GitTags(MagicMock()).all()
            unreleased_tag = next(tags)
            self.assertIsNone(unreleased_tag.tagger)
            self.assertIsNone(unreleased_tag.created)


