import unittest
import shutil
import os
from tools.csvreportcreator import DictionaryListCsvExporter
from tools.csvreportcreator import DictionaryCsvExporter
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

class TestDictionaryListCsvExporte(BasicTestExporter):

    def testAuthorDictExport(self):
        #test with dict
        exporter = DictionaryListCsvExporter()
        file_name = os.path.join(self.csv_outputdir, 'authors.csv')
        additional = {'projectname': 'Project Name Unit test', 'reponame': 'repostat'}
        exporter.export(file_name, self.gs.authors, additional)
        self.assertTrue(os.path.isfile(file_name))
        self.assertTrue('Viktor Kopp;4028;3238' in open(file_name).read())

    def testCommitListExport(self):
        #test with list
        exporter = DictionaryListCsvExporter()
        file_name = os.path.join(self.csv_outputdir, 'commits.csv')
        additional = {'projectname': 'Project Name Unit test', 'reponame': 'repostat'}
        exporter.export(file_name, self.gs.commits, additional)
        self.assertTrue(os.path.isfile(file_name))
        self.assertTrue('Viktor Kopp;8;5;2018-10-15' in open(file_name).read())


class TestGeneralDictionaryCsvExporter(BasicTestExporter):

    def testGeneralDictionaryCsvExporterWithoutKey(self):
        exporter = DictionaryCsvExporter()
        file_name = os.path.join(self.csv_outputdir, 'general_dict_export_withoutKey.csv')
        test_data = {}
        for i in range (0, 10):
            test_data[i] = {'projectname': 'Project Name Unit test', 'reponame': 'repostat'}
        exporter.export(file_name, test_data, False)
        self.assertTrue(os.path.isfile(file_name))
        self.assertTrue('projectname;reponame' in open(file_name).read())

    def testGeneralDictionaryCsvExporterWithKeyDefault(self):
        exporter = DictionaryCsvExporter()
        file_name = os.path.join(self.csv_outputdir, 'general_dict_export_withkeydef.csv')
        test_data = {}
        for i in range (0, 10):
            test_data[i] = {'projectname': 'Project Name Unit test', 'reponame': 'repostat'}
        exporter.export(file_name, test_data)
        self.assertTrue(os.path.isfile(file_name))
        self.assertTrue('projectname;reponame;key' in open(file_name).read())
        self.assertTrue('Project Name Unit test;repostat;0' in open(file_name).read())

    def testGeneralDictionaryCsvExporterWithKeyUnit(self):
        exporter = DictionaryCsvExporter()
        file_name = os.path.join(self.csv_outputdir, 'general_dict_export_withkeyunit.csv')
        test_data = {}
        for i in range (0, 10):
            test_data[i] = {'projectname': 'Project Name Unit test', 'reponame': 'repostat'}
        exporter.export(file_name, test_data, True, 'Key UnitTestField')
        self.assertTrue(os.path.isfile(file_name))
        self.assertTrue('projectname;reponame;Key UnitTestField' in open(file_name).read())
        self.assertTrue('Project Name Unit test;repostat;0' in open(file_name).read())
