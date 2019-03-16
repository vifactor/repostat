import unittest
import os
from tools.reportCreator  import ReportCreator
from tools.gitstatistics import GitStatistics

conf = {
    'max_domains': 10,
    'max_ext_length': 10,
    'style': 'gitstats.css',
    'max_authors': 7,
    'max_authors_of_months': 6,
    'authors_top': 5,
    'commit_begin': '',
    'commit_end': 'HEAD',
    'linear_linestats': 1,
    'project_name': '',
    'processes': 8,
    'start_date': '',
    'output':'html'
}

class TestReportCreator(unittest.TestCase):
    gs = None
    csv_outputdir = os.path.join(os.path.dirname(os.path.abspath(__file__)) , "csv_outs")

    def setUp(self):
        this_file_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
        print('Init git repo. Path:' + this_file_dir)
        self.gs = GitStatistics(this_file_dir)

    def testReportCreatorRepoName(self):
        report = ReportCreator()
        conf['project_name'] = ''
        report.create(self.gs, self.csv_outputdir, conf)
        self.assertEqual(self.gs.reponame, "repostat")
        self.assertEqual(self.gs.reponame, report.projectname)
        self.assertEqual(report.title, report.projectname)

    def testReportCreatorProjectName(self):
        report = ReportCreator()
        conf['project_name'] = 'New project name'
        report.create(self.gs, self.csv_outputdir, conf)
        self.assertEqual(self.gs.reponame, "repostat")
        self.assertEqual(conf['project_name'], report.projectname)
        self.assertEqual(report.title, report.projectname)

if __name__ == '__main__':
    unittest.main()