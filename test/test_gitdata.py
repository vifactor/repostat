import unittest
from pygit2 import Signature

import test
from analysis.gitdata import WholeHistory, LinearHistory


class GitHistoryTest(unittest.TestCase):
    def setUp(self):
        self.test_repo = test.GitRepository()

        # create commit in master branch (created by default)
        self.test_repo.commit_builder \
            .set_author("John Doe", "john@doe.com") \
            .add_file(content="bzyk") \
            .commit()

    def test_records_count_in_history(self):
        # create second branch from 'master' (which already had one commit)
        branch = self.test_repo.branches.local.create('second_branch', self.test_repo.head.peel())
        self.test_repo.checkout(branch)

        # create commit on new branch
        self.test_repo.commit_builder \
            .set_author("Author Author", "author@author.net") \
            .add_file(content=["some content"]) \
            .commit()

        # so far no merge commits, both linear and whole history caches should contain 2 records
        whole_history_df = WholeHistory(self.test_repo).as_dataframe()
        self.assertEqual(2, len(whole_history_df.index))
        linear_history_df = LinearHistory(self.test_repo).as_dataframe()
        self.assertEqual(2, len(linear_history_df.index))

        # now merge commit is being created
        # checkout to master
        master_branch = self.test_repo.branches.get('master')
        self.test_repo.checkout(master_branch)
        # and merge 'second_branch' into 'master'
        self.test_repo.merge(self.test_repo.branches.get('second_branch').peel().id)
        # by creating merge commit
        author = Signature("name", "email")
        committer = author
        tree = self.test_repo.index.write_tree()
        message = "Merge 'second_branch' into 'master'"
        self.test_repo.create_commit('HEAD', author, committer, message, tree,
                                     [self.test_repo.head.target,
                                      self.test_repo.branches.get('second_branch').peel().oid])

        # whole history cache should contain 3 records: initial commit + commit in merged branch + merge commit
        whole_history_df = WholeHistory(self.test_repo).as_dataframe()
        self.assertEqual(3, len(whole_history_df.index))
        # linear history cache still contains 2 records: initial commit + merge commit
        linear_history_df = LinearHistory(self.test_repo).as_dataframe()
        self.assertEqual(2, len(linear_history_df.index))


if __name__ == '__main__':
    unittest.main()
