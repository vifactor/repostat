import unittest

from analysis import GitStatistics
import test


class TestSingleCommitRepository(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.git_repository = test.GitRepository()

        cls.git_repository.commit_builder\
            .set_author("John Doe", "john@doe.com")\
            .add_file()\
            .commit()

        cls.commit_author, = cls.git_repository.commit_builder.author_signatures
        cls.gs = GitStatistics(cls.git_repository.location)

    def test_missing_authors_email(self):
        import tempfile
        import os
        from test import shellhelper

        cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as tmpdir:
            # change working directory
            os.chdir(tmpdir)
            shellhelper.get_pipe_output(['git init'])
            shellhelper.get_pipe_output(['touch file.txt'])
            shellhelper.get_pipe_output(['git add file.txt'])
            # apparently it is not possible to create pygit.Signature with empty author's email (and name)
            # but commits with no author's email can be created via git
            shellhelper.get_pipe_output(['git commit -m "No-email author" --author "Author NoEmail <>"'])
            try:
                # Commit without author's email does not crash statistics calculation
                GitStatistics(tmpdir)
            except Exception as e:
                self.fail(str(e))
            os.chdir(cwd)
