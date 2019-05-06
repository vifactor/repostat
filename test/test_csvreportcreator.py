import unittest
import shutil
import os
from tools.csvreportcreator import DictionaryListCsvExporter
from tools.csvreportcreator import DictionaryCsvExporter
from tools.gitstatistics import GitStatistics


class BasicTestExporter(unittest.TestCase):
    gs = None
    csv_outputdir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "csv_outs")

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
        # test with dict
        exporter = DictionaryListCsvExporter()
        file_name = os.path.join(self.csv_outputdir, 'authors.csv')
        additional = {'projectname': 'Project Name Unit test', 'reponame': 'repostat'}
        exporter.export(file_name, self.gs.authors, False, additional)
        self.assertTrue(os.path.isfile(file_name))
        # Pekka Enberg an old contributor with one commit. These test data maybe will not change in the future
        self.assertTrue('Pekka Enberg;1;1;' in open(file_name, encoding='utf-8').read())

    def testCommitListExport(self):
        # test with list
        exporter = DictionaryListCsvExporter()
        file_name = os.path.join(self.csv_outputdir, 'commits.csv')
        additional = {'projectname': 'Project Name Unit test', 'reponame': 'repostat'}
        exporter.export(file_name, self.gs.all_commits, False, additional)
        self.assertTrue(os.path.isfile(file_name))
        self.assertTrue('4;0;False;1539590122;2018-10-15 09:55:22' in open(file_name, encoding='utf-8').read())

    def testAuthorDictExportAppend(self):
        # test with dict
        exporter = DictionaryListCsvExporter()
        file_name = os.path.join(self.csv_outputdir, 'authors.csv')
        exporter.export(file_name, self.gs.authors, False)
        statinfo_before = os.stat(file_name)
        exporter.export(file_name, self.gs.authors, True)
        statinfo_after = os.stat(file_name)
        self.assertTrue(statinfo_after.st_size > statinfo_before.st_size)

    def testAuthorDictExportAppendFalse(self):
        # test with dict
        exporter = DictionaryListCsvExporter()
        file_name = os.path.join(self.csv_outputdir, 'authors.csv')
        exporter.export(file_name, self.gs.authors, False)
        statinfo_before = os.stat(file_name)
        exporter.export(file_name, self.gs.authors, False)
        statinfo_after = os.stat(file_name)
        self.assertTrue(statinfo_after.st_size == statinfo_before.st_size)


class TestGeneralDictionaryCsvExporter(BasicTestExporter):

    def testGeneralDictionaryCsvExporterWithoutKey(self):
        exporter = DictionaryCsvExporter()
        file_name = os.path.join(self.csv_outputdir, 'general_dict_export_withoutKey.csv')
        test_data = {}
        for i in range(0, 10):
            test_data[i] = {'projectname': 'Project Name Unit test', 'reponame': 'repostat'}
        exporter.export(file_name, test_data, False)
        self.assertTrue(os.path.isfile(file_name))
        self.assertTrue('projectname;reponame' in open(file_name, encoding='utf-8').read())

    def testGeneralDictionaryCsvExporterWithKeyDefaultAndSpecChars(self):
        exporter = DictionaryCsvExporter()
        file_name = os.path.join(self.csv_outputdir, 'general_dict_export_withkeydef.csv')
        test_data = {}
        for i in range(0, 10):
            test_data[i] = {'projectname': 'Project Name Unit test', 'reponame': 'repostat',
                            'special-chars-hu': 'árvíztűrőtükörfúrógépÁRVÍZTŰRŐTÜKÖRFÚRÓGÉP',
                            'special-chars-de': 'ẞÄÖÜäöüß'}
        exporter.export(file_name, test_data)
        self.assertTrue(os.path.isfile(file_name))
        self.assertTrue(
            'projectname;reponame;special-chars-hu;special-chars-de;key' in open(file_name, encoding='utf-8').read())
        self.assertTrue(
            'Project Name Unit test;repostat;árvíztűrőtükörfúrógépÁRVÍZTŰRŐTÜKÖRFÚRÓGÉP;ẞÄÖÜäöüß;0' in
            open(file_name, encoding='utf-8').read())

    def testGeneralDictionaryCsvExporterWithKeyUnit(self):
        exporter = DictionaryCsvExporter()
        file_name = os.path.join(self.csv_outputdir, 'general_dict_export_withkeyunit.csv')
        test_data = {}
        for i in range(0, 10):
            test_data[i] = {'projectname': 'Project Name Unit test', 'reponame': 'repostat'}
        exporter.export(file_name, test_data, False, True, 'Key UnitTestField')
        self.assertTrue(os.path.isfile(file_name))
        self.assertTrue('projectname;reponame;Key UnitTestField' in open(file_name, encoding='utf-8').read())
        self.assertTrue('Project Name Unit test;repostat;0' in open(file_name, encoding='utf-8').read())

    def testGeneralDictionaryCsvExporterAppend(self):
        exporter = DictionaryCsvExporter()
        file_name = os.path.join(self.csv_outputdir, 'general_dict_export_append.csv')
        test_data = {}
        for i in range(0, 10):
            test_data[i] = {'projectname': 'Project Name Unit test', 'reponame': 'repostat'}
        exporter.export(file_name, test_data, False)
        exporter.export(file_name, self.gs.authors, False)
        statinfo_before = os.stat(file_name)
        exporter.export(file_name, self.gs.authors, True)
        statinfo_after = os.stat(file_name)
        self.assertTrue(statinfo_after.st_size > statinfo_before.st_size)

    def testGeneralDictionaryCsvExporterAppendFalse(self):
        exporter = DictionaryCsvExporter()
        file_name = os.path.join(self.csv_outputdir, 'general_dict_export_appendfalse.csv')
        test_data = {}
        for i in range(0, 10):
            test_data[i] = {'projectname': 'Project Name Unit test', 'reponame': 'repostat'}
        exporter.export(file_name, test_data, False)
        exporter.export(file_name, self.gs.authors, False)
        statinfo_before = os.stat(file_name)
        exporter.export(file_name, self.gs.authors, False)
        statinfo_after = os.stat(file_name)
        self.assertTrue(statinfo_after.st_size == statinfo_before.st_size)
