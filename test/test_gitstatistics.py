import unittest
import datetime
from tools.gitstatistics import CommitDictFactory

class TestCommitDictFactory(unittest.TestCase):
	
	def setUp(self):
		pass
	
	def testCreateCommitAuthorName(self):
		commit = CommitDictFactory.create_commit('Test Author', 1, 2, datetime.datetime.now().timestamp())
		self.assertEqual(commit[CommitDictFactory.AUTHOR_NAME], 'Test Author')

	def testCreateCommitLinesAdded(self):
		commit = CommitDictFactory.create_commit('Test Author', 1, 2, datetime.datetime.now().timestamp())
		self.assertEqual(commit[CommitDictFactory.LINES_ADDED], 1)

	def testCreateCommitLinesRemoved(self):
		commit = CommitDictFactory.create_commit('Test Author', 1, 2, datetime.datetime.now().timestamp())
		self.assertEqual(commit[CommitDictFactory.LINES_REMOVED], 2)

	def testCreateCommitTimeStamp(self):
		ts = datetime.datetime.now().timestamp()
		commit = CommitDictFactory.create_commit('Test Author', 1, 2, ts)
		self.assertEqual(commit[CommitDictFactory.TIMESTAMP], ts)

if __name__ == '__main__':
	unittest.main()