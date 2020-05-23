import subprocess
import unittest
import os
from collections import defaultdict
from pygit2 import Signature, Repository
import pygit2

from analysis.gitdata import WholeHistory, LinearHistory, BlameData, FilesData, TagsData
from analysis.gitrepository import GitRepository
from analysis.tests.gitrepository import GitTestRepository


class GitHistoryTest(unittest.TestCase):
    def setUp(self):
        self.test_repo = GitTestRepository()

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

    def test_repository_name(self):
        _, expected_name = os.path.split(self.test_repo.location)
        repo = GitRepository(self.test_repo.location)
        self.assertEqual(expected_name, repo.name)


class GitSnapshotTest(unittest.TestCase):
    def setUp(self):
        self.test_repo = GitTestRepository()

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
            .add_file(filename="xxx.xxx", content=["You", "shall", "not", "pass"]) \
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

    def test_blame_records_content(self):
        snapshot_data = BlameData(self.test_repo).fetch()
        recs = self.records_for_author(snapshot_data)
        self.assertCountEqual(recs["Jack Dau"], [(2, 'jacksfile.txt')])
        self.assertCountEqual(recs["John Snow"], [(3, 'jacksfile.txt'), (1, 'johnsfile.txt')])
        self.assertCountEqual(recs["John Doe"], [(1, 'jd.dat')])
        self.assertCountEqual(recs["Abc Abc"], [(2, 'abc.doc')])

    def test_blame_records_content_with_mailmap(self):
        real_author = ("John Snow", "john@snow.com")
        pseudo_author = ("John Doe", "random@random.rnd")
        with open(os.path.join(self.test_repo.location, ".mailmap"), 'w') as mm:
            mm.write(f"{real_author[0]} <{real_author[1]}> "
                     f"{pseudo_author[0]} <{pseudo_author[1]}>")
        snapshot_data = BlameData(self.test_repo).fetch()
        recs = self.records_for_author(snapshot_data)
        self.assertCountEqual(recs["John Snow"], [(3, 'jacksfile.txt'), (1, 'johnsfile.txt'), (1, 'jd.dat')])

    def test_files_records_content(self):
        files_data = FilesData(self.test_repo)._fetch()
        expected_files_data = {
            "abc.doc": 2,
            "jacksfile.txt": 5,
            "jd.dat": 1,
            "johnsfile.txt": 1,
            "xxx.xxx": 4
        }

        self.assertEqual(len(expected_files_data), len(files_data))
        for file_data in files_data:
            filename = file_data["file"]
            self.assertEqual(expected_files_data[filename], file_data["lines_count"])

            file_abs_path = os.path.join(self.test_repo.location, filename)
            self.assertEqual(os.stat(file_abs_path).st_size, file_data["size_bytes"])


class IncompleteSignaturesTest(unittest.TestCase):

    def test_incomplete_signature_does_not_crash_gitdata_classes(self):
        import tempfile

        with tempfile.TemporaryDirectory(prefix="tmprepo_") as tmp_repo_location:
            # change working directory
            os.chdir(tmp_repo_location)
            subprocess.run(['git', 'init'], cwd=tmp_repo_location)
            # create a file a single line in it
            filename = 'file.txt'
            with open(os.path.join(tmp_repo_location, filename), "w") as f:
                f.write("A single line of code\n")
            subprocess.run(['git', 'add', 'file.txt'], cwd=tmp_repo_location)
            # apparently it is not possible to create pygit.Signature with empty author's email (and name)
            # but commits with no author's email can be created via git
            subprocess.run(['git', 'commit', '-m "No-email author" --author "Author NoEmail <>"'],
                           cwd=tmp_repo_location)
            try:
                # Commit without author's email does not crash data fetch
                git_repository = Repository(tmp_repo_location)
                WholeHistory(git_repository)
                BlameData(git_repository)
            except Exception as e:
                self.fail(str(e))


class TagsDataTest(unittest.TestCase):

    def test_annotated_tags_fetch(self):
        test_repo = GitTestRepository()

        # master branch
        test_repo.commit_builder \
            .set_author("John Doe", "john@doe.com") \
            .add_file(content="bzyk") \
            .commit()

        # create second branch from 'master' (which already had one commit)
        branch = test_repo.branches.local.create('second_branch', test_repo.head.peel())
        test_repo.checkout(branch)

        # create commit on new branch
        test_repo.commit_builder \
            .set_author("Author Author", "author@author.net") \
            .add_file(content=["some content"]) \
            .commit()

        # checkout to master
        master_branch = test_repo.branches.get('master')
        test_repo.checkout(master_branch)
        # create commit
        test_repo.commit_builder \
            .set_author("Jack Johns", "jack@johns.com").add_file() \
            .commit()

        # and merge 'second_branch' into 'master'
        test_repo.merge(test_repo.branches.get('second_branch').peel().id)
        # by creating merge commit
        author = Signature("name", "email")
        committer = author
        tree = test_repo.index.write_tree()
        message = "Merge 'second_branch' into 'master'"
        v1_oid = test_repo.create_commit('HEAD', author, committer, message, tree,
                                         [test_repo.head.target,
                                          test_repo.branches.get('second_branch').peel().oid])

        test_repo.create_tag("v1", str(v1_oid), pygit2.GIT_OBJ_COMMIT,
                             Signature('John Doe', 'jdoe@example.com', 1589748740, 0),
                             "v1 tag")

        v2_oid = test_repo.commit_builder \
            .set_author("Jack Johns", "jack@johns.com").add_file() \
            .commit()
        test_repo.create_tag("v2", str(v2_oid), pygit2.GIT_OBJ_COMMIT,
                             Signature('John Doe', 'jdoe@example.com'),
                             "v2 tag")

        test_repo.commit_builder \
            .set_author("Incognito", "j@anonimous.net").add_file() \
            .commit()

        tags_data = TagsData(test_repo).fetch()

        self.assertEqual(4, len([x for x in tags_data if x['tag_name'] == 'v1']))
        self.assertEqual(1, len([x for x in tags_data if x['tag_name'] == 'v2']))
        self.assertEqual(1, len([x for x in tags_data if x['tag_name'] is None]))

    def test_unannotated_tag(self):
        test_repo = GitTestRepository()

        oid = test_repo.commit_builder \
            .set_author("John Doe", "john@doe.com") \
            .add_file(content="bzyk") \
            .commit()

        # this creates an unannotated tag (symbolic tag)
        test_repo.references.create('refs/tags/version1', oid)
        tags_data = TagsData(test_repo).fetch()
        self.assertEqual(1, len(tags_data))
        tag_data = tags_data[0]
        self.assertIsNone(tag_data['tagger_name'])
        self.assertEqual(-1, tag_data['tagger_time'])
