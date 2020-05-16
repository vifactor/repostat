import unittest

import tools


class TestTools(unittest.TestCase):

    def test_get_file_extension(self):
        self.assertEqual('extension', tools.get_file_extension("folder/filename.extension"))
        self.assertEqual('.extension', tools.get_file_extension("folder/.extension"))
        self.assertEqual('extension', tools.get_file_extension("folder/filename.suffix.extension"))
        self.assertEqual('FILENAME', tools.get_file_extension("folder/FILENAME"))
        self.assertEqual('extension', tools.get_file_extension("folder/.filename.suffix.extension"))
