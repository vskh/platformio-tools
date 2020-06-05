#!/usr/bin/env python3

import unittest
from generate_pio_build import expand


class ExpandTests(unittest.TestCase):
    test_def_index = {'test1': "1", 'test2': "2", 'test3': "3"}

    def test_expands_single(self):
        var = 'test1'
        expansion = expand("{{{}}}".format(var), self.test_def_index)
        self.assertEqual(expansion, self.test_def_index[var])

    def test_expands_multiple(self):
        expansion = expand("test = {test1} {test2}", self.test_def_index)
        self.assertEqual(expansion, "test = 1 2")

    def test_leaves_unknown_as_is(self):
        expansion = expand("test = {test3} {test5}", self.test_def_index)
        self.assertEqual(expansion, "test = 3 {test5}")


if __name__ == "__main__":
    unittest.main()
