import unittest
import datetime
import os
from tools.gitstatistics import CommitDictFactory
from tools.gitstatistics import AuthorDictFactory
from tools.gitstatistics import GitStatistics


class TestCommitDictFactory(unittest.TestCase):

    def setUp(self):
        pass

    def testCreateCommitAuthorName(self):
        commit = CommitDictFactory.create_commit('Test Author', 1, 2, '2019.03.15', datetime.datetime.now().timestamp())
        self.assertEqual(commit[CommitDictFactory.AUTHOR_NAME], 'Test Author')
        self.assertEqual(commit[CommitDictFactory.AUTHOR_NAME], CommitDictFactory.get_author(commit))

    def testCreateCommitLinesAdded(self):
        commit = CommitDictFactory.create_commit('Test Author', 1, 2, '2019.03.15', datetime.datetime.now().timestamp())
        self.assertEqual(commit[CommitDictFactory.LINES_ADDED], 1)
        self.assertEqual(commit[CommitDictFactory.LINES_ADDED], CommitDictFactory.get_lines_added(commit))

    def testCreateCommitLinesRemoved(self):
        commit = CommitDictFactory.create_commit('Test Author', 1, 2, '2019.03.15', datetime.datetime.now().timestamp())
        self.assertEqual(commit[CommitDictFactory.LINES_REMOVED], 2)
        self.assertEqual(commit[CommitDictFactory.LINES_REMOVED], CommitDictFactory.get_lines_removed(commit))

    def testCreateCommitTimeStamp(self):
        ts = datetime.datetime.now().timestamp()
        commit = CommitDictFactory.create_commit('Test Author', 1, 2, '2019.03.15', ts)
        self.assertEqual(commit[CommitDictFactory.TIMESTAMP], ts)
        self.assertEqual(commit[CommitDictFactory.TIMESTAMP], CommitDictFactory.get_time_stamp(commit))


class TestAuthorDictFactory(unittest.TestCase):
    testData = {}

    def setUp(self):
        first_commit: datetime = datetime.datetime.strptime('2019-01-01', '%Y-%m-%d')
        last_commit = datetime.datetime.strptime('2019-03-15', '%Y-%m-%d')
        self.testData['basic'] = {
            'first_commit_ts': first_commit.timestamp(),
            'last_commit_ts': last_commit.timestamp(),
            'author_name': 'Test Author',
            'active_days': '2015-03-01',
            'lines_added': 1000,
            'lines_removed': 100,
            'commits': 50}

    @staticmethod
    def create_test_author(data):
        return AuthorDictFactory.create_author(data['author_name'], data['lines_removed'], data['lines_added'],
                                               data['active_days'], data['commits'], data['first_commit_ts'],
                                               data['last_commit_ts'])

    def getTestAuthor(self):
        return self.create_test_author(self.testData['basic'])

    def testAuthorCreateDict(self):
        author = self.getTestAuthor()
        active_days = author[AuthorDictFactory.ACTIVE_DAYS]
        self.assertTrue(active_days.__len__() == 1)
        self.assertTrue('2015-03-01' in active_days)
        self.assertEqual(author[AuthorDictFactory.AUTHOR_NAME], self.testData['basic']['author_name'])
        self.assertEqual(author[AuthorDictFactory.COMMITS], self.testData['basic']['commits'])
        self.assertEqual(author[AuthorDictFactory.FIRST_COMMIT], self.testData['basic']['first_commit_ts'])
        self.assertEqual(author[AuthorDictFactory.LAST_COMMIT], self.testData['basic']['last_commit_ts'])
        self.assertEqual(author[AuthorDictFactory.LINES_ADDED], self.testData['basic']['lines_added'])
        self.assertEqual(author[AuthorDictFactory.LINES_REMOVED], self.testData['basic']['lines_removed'])

    def testAuthorAddActiveDay(self):
        author = self.getTestAuthor()
        active_days = author[AuthorDictFactory.ACTIVE_DAYS]
        day_count = active_days.__len__()
        AuthorDictFactory.add_active_day(author, '2000.01.01')
        self.assertEqual(author[AuthorDictFactory.ACTIVE_DAYS].__len__(), day_count + 1)
        self.assertTrue('2000.01.01' in author[AuthorDictFactory.ACTIVE_DAYS])

    def testAuthorLinesAdd(self):
        author = self.getTestAuthor()
        init = author[AuthorDictFactory.LINES_ADDED]
        AuthorDictFactory.add_lines_added(author, 10)
        self.assertEqual(author[AuthorDictFactory.LINES_ADDED], init + 10)

    def testAuthorLinesRemoved(self):
        author = self.getTestAuthor()
        init = author[AuthorDictFactory.LINES_REMOVED]
        AuthorDictFactory.add_lines_removed(author, 13)
        self.assertEqual(author[AuthorDictFactory.LINES_REMOVED], init + 13)

    def testAuthorLinesCommit(self):
        author = self.getTestAuthor()
        init = author[AuthorDictFactory.COMMITS]
        AuthorDictFactory.add_commit(author, 10)
        self.assertEqual(author[AuthorDictFactory.COMMITS], init + 10)

    def testAuthorCheckFirstCommit(self):
        author = self.getTestAuthor()
        init = author[AuthorDictFactory.FIRST_COMMIT]

        # expected: first_commit not change
        AuthorDictFactory.check_first_commit_stamp(author, init + 1000)
        self.assertEqual(author[AuthorDictFactory.FIRST_COMMIT], init)

        # expected: first_commit change to the earlier timestamp
        AuthorDictFactory.check_first_commit_stamp(author, init - 1000)
        self.assertEqual(author[AuthorDictFactory.FIRST_COMMIT], init - 1000)

    def testAuthorLastCommit(self):
        author = self.getTestAuthor()
        init = author[AuthorDictFactory.LAST_COMMIT]
        last_commit_after = datetime.datetime.strptime('2019-03-20', '%Y-%m-%d')
        last_commit_before = datetime.datetime.strptime('2019-03-10', '%Y-%m-%d')

        # expected: first_commit not change
        AuthorDictFactory.check_last_commit_stamp(author, last_commit_before.timestamp())
        self.assertEqual(author[AuthorDictFactory.LAST_COMMIT], init)

        # expected: first_commit change to the earlier timestamp
        AuthorDictFactory.check_last_commit_stamp(author, last_commit_after.timestamp())
        self.assertEqual(author[AuthorDictFactory.LAST_COMMIT], last_commit_after.timestamp())
        self.assertEqual(author[AuthorDictFactory.LAST_ACTIVE_DAY], '2019-03-20')


class TestGitStatistics(unittest.TestCase):

    @staticmethod
    def get_gitstatistic():
        this_file_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
        print('Init git repo. Path:' + this_file_dir)
        return GitStatistics(this_file_dir)

    def tesFetchAllCommits(self):
        gs = TestGitStatistics.get_gitstatistic()
        commits = dict()
        gs.fetch_all_commits(commits)
        print("Commit count {}".format(commits.__len__()))

    def testFetchAuthorInfo(self):
        gs = TestGitStatistics.get_gitstatistic()
        authors = {}
        commits = {}
        gs.fetch_authors_info(authors, commits)
        print("Commit count {}".format(len(commits)))


if __name__ == '__main__':
    unittest.main()
