import unittest
import os
from collections import defaultdict
from pygit2 import Signature

import test
from analysis.gitdata import WholeHistory, LinearHistory, RevisionData


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

        # check merge commits count (there is a single merge commit)
        self.assertEqual(1, whole_history_df['is_merge_commit'].sum())

    def test_mailmap(self):
        # create second commit with another signature
        self.test_repo.commit_builder \
            .set_author("Author Author", "author@author.net") \
            .add_file(content=["some content"]) \
            .commit()

        # map second author's signature as first one using mailmap file
        commit_author1, commit_author2 = self.test_repo.commit_builder.author_signatures
        with open(os.path.join(self.test_repo.location, ".mailmap"), 'w') as mm:
            mm.write(f"{commit_author1.name} <{commit_author1.email}> "
                     f"{commit_author2.name} <{commit_author2.email}>")

        # Mailmap might be tested either on Whole or Linear history
        wh_df = WholeHistory(self.test_repo).as_dataframe()

        authors = wh_df['author_name'].unique()
        self.assertCountEqual(["John Doe"], authors)
        emails = wh_df['author_email'].values
        # both emails are preserved for statistics
        self.assertCountEqual(["john@doe.com", "author@author.net"], emails)

    # TODO: add test for inserted/deleted lines count


class GitSnapshotTest(unittest.TestCase):
    def setUp(self):
        self.test_repo = test.GitRepository()

        self.test_repo.commit_builder \
            .set_author("Jack Dau", "jack@dau.org") \
            .add_file(filename="jacksfile.txt", content=["JackJack", "DauDau"]) \
            .commit()

        self.test_repo.commit_builder \
            .set_author("John Snow", "john@snow.com") \
            .append_file(filename="jacksfile.txt", content=["Winter", "is", "coming"]) \
            .commit()

        self.test_repo.commit_builder \
            .set_author("John Snow", "john@snow.com") \
            .add_file(filename="johnsfile.txt", content=["bzyk"]) \
            .commit()

        self.test_repo.commit_builder \
            .set_author("Gandalf", "gandalf@castle.ua") \
            .add_file(content=["You", "shall", "not", "pass"]) \
            .commit()

        self.test_repo.commit_builder \
            .set_author("John Doe", "random@random.rnd") \
            .add_file(filename="jd.dat", content=["Random"]) \
            .commit()

        self.test_repo.commit_builder \
            .set_author("Abc Abc", "abc@abc.io") \
            .add_file(filename="abc.doc", content=["Abc", "Abc"]) \
            .commit()

    @staticmethod
    def records_for_author(snapshot_data):
        recs = defaultdict(list)
        for name, lines, time, file in snapshot_data:
            recs[name].append((lines, file))
        return recs

    def test_records_content(self):
        snapshot_data = RevisionData(self.test_repo).fetch()
        recs = self.records_for_author(snapshot_data)
        self.assertCountEqual(recs["Jack Dau"], [(2, 'jacksfile.txt')])
        self.assertCountEqual(recs["John Snow"], [(3, 'jacksfile.txt'), (1, 'johnsfile.txt')])
        self.assertCountEqual(recs["John Doe"], [(1, 'jd.dat')])
        self.assertCountEqual(recs["Abc Abc"], [(2, 'abc.doc')])

    def test_records_content_with_mailmap(self):
        real_author = ("John Snow", "john@snow.com")
        pseudo_author = ("John Doe", "random@random.rnd")
        with open(os.path.join(self.test_repo.location, ".mailmap"), 'w') as mm:
            mm.write(f"{real_author[0]} <{real_author[1]}> "
                     f"{pseudo_author[0]} <{pseudo_author[1]}>")
        snapshot_data = RevisionData(self.test_repo).fetch()
        recs = self.records_for_author(snapshot_data)
        self.assertCountEqual(recs["John Snow"], [(3, 'jacksfile.txt'), (1, 'johnsfile.txt'), (1, 'jd.dat')])
