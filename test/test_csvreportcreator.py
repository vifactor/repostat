import unittest
import shutil
import os
from tools.csvreportcreator   import AuthorCsvExporter
from tools.csvreportcreator   import CommitCsvExporter
from tools.csvreportcreator import CSVReportCreator
from tools.gitstatistics import GitStatistics

class BasicTestExporter(unittest.TestCase):
    gs = None
    csv_outputdir = os.path.join(os.path.dirname(os.path.abspath(__file__)) , "csv_outs")

    def setUp(self):
        try:
            shutil.rmtree(self.csv_outputdir)
        except OSError:
            pass
        os.makedirs(self.csv_outputdir)
        this_file_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
        print('Init git repo. Path:' + this_file_dir)
        self.gs = GitStatistics(this_file_dir)

class TestAuthorExporter(BasicTestExporter):

    def testAuthorExport(self):
        exporter = AuthorCsvExporter()
        fileName = os.path.join(self.csv_outputdir, 'authors.csv')
        additional = {'projectname': 'Project Name Unit test', 'reponame': 'repostat'}
        exporter.exportAuthors(fileName, self.gs.authors, additional)
        self.assertTrue(os.path.isfile(fileName))
        self.assertTrue('Viktor Kopp;4028;3238' in open(fileName).read())

class TestCommitExporter(BasicTestExporter):

    def testCommitExport(self):
        exporter = CommitCsvExporter()
        fileName = os.path.join(self.csv_outputdir, 'commits.csv')
        additional = {'projectname': 'Project Name Unit test', 'reponame': 'repostat'}
        exporter.exportCommits(fileName, self.gs.commits, additional)
        self.assertTrue(os.path.isfile(fileName))
        self.assertTrue('Viktor Kopp;5;8;2018-10-15' in open(fileName).read())

