#!/usr/bin/env python3

import unittest
import re
import generate_pio_build as gpb


class ReadPlatformDefTests(unittest.TestCase):
    def test_expands_dots_in_format_placeholders(self):
        platform_def = gpb.read_platform_def(
            "./vendor/devkit-sdk/AZ3166/src/platform.txt")

        test_key = "compiler_S_flags"
        self.assertIn(test_key, platform_def)

        val = platform_def[test_key].strip()

        self.assertEqual(
            val, '-c -x assembler-with-cpp {compiler_libstm_c_flags} -DTRANSACTION_QUEUE_SIZE_SPI=2 -D__CORTEX_M4 -DUSB_STM_HAL -DARM_MATH_CM4 -D__FPU_PRESENT=1 -DUSBHOST_OTHER -D__MBED_CMSIS_RTOS_CM -D__CMSIS_RTOS')


class ExpandTests(unittest.TestCase):
    test_def_index = {'test1': "1", 'test2': "2", 'test3': "3"}

    def test_expands_single(self):
        var = 'test1'
        expansion = gpb.expand("{{{}}}".format(var), self.test_def_index)
        self.assertEqual(expansion, self.test_def_index[var])

    def test_expands_multiple(self):
        expansion = gpb.expand("test = {test1} {test2}", self.test_def_index)
        self.assertEqual(expansion, "test = 1 2")

    def test_leaves_unknown_as_is(self):
        expansion = gpb.expand("test = {test3} {test5}", self.test_def_index)
        self.assertEqual(expansion, "test = 3 {test5}")


class ExpandDictTests(unittest.TestCase):
    test_def_index = {'test1': "1", 'test2': "2", 'test3': "3"}

    def test_expands_dict_of_strings(self):
        source_dict = {'t1': "{test1}"}
        expected_dict = {'t1': "1"}
        self.assertEqual(gpb.expand_dict(
            source_dict, self.test_def_index), expected_dict)

    def test_expands_dict_of_tuples(self):
        source_dict = {'t1': ("{test1}", "{test2}", "test3")}
        expected_dict = {'t1': ("1", "2", "test3")}
        self.assertEqual(gpb.expand_dict(
            source_dict, self.test_def_index), expected_dict)

    def test_expands_dict_of_lists(self):
        source_dict = {'t1': ["{test1}", "{test2}", "test3"]}
        expected_dict = {'t1': ["1", "2", "test3"]}
        self.assertEqual(gpb.expand_dict(
            source_dict, self.test_def_index), expected_dict)

    def test_expands_dict_keys(self):
        source_dict = {'t{test1}': "test"}
        expected_dict = {'t1': "test"}
        self.assertEqual(gpb.expand_dict(
            source_dict, self.test_def_index), expected_dict)


class ExtractExpandedRecipesTests(unittest.TestCase):
    def test_simple_expansion_works(self):
        test_platform_def = {
            'test1': "gcc",
            'test2': "g++",
            'test3': "as",
            'test4': "ld",
            'test5': "ar",
            'recipe_c_o_pattern': "{test1} myfile",
            'recipe_cpp_o_pattern': "{test2} myfile",
            'recipe_S_o_pattern': "{test3} myfile",
            'recipe_c_combine_pattern': "{test4} myfile",
            'recipe_ar_pattern': "{test5} myfile"
        }
        expected_recipes = {
            'recipe_c_o_pattern': ["gcc", "myfile"],
            'recipe_cpp_o_pattern': ["g++", "myfile"],
            'recipe_S_o_pattern': ["as", "myfile"],
            'recipe_c_combine_pattern': ["ld", "myfile"],
            'recipe_ar_pattern': ["ar", "myfile"]
        }
        recipes = gpb.extract_expanded_recipes(test_platform_def)
        self.assertDictEqual(expected_recipes, recipes)

    def test_recursive_expansion_works(self):
        test_platform_def = {
            'extra_flags': 'extraflag',
            'cmd': 'compiler {extra_flags}',
            'recipe_c_o_pattern': "{cmd} myfile",
            'recipe_cpp_o_pattern': "{recipe_c_o_pattern}",
            'recipe_S_o_pattern': "{recipe_c_o_pattern}",
            'recipe_c_combine_pattern': "{recipe_c_o_pattern}",
            'recipe_ar_pattern': "{recipe_c_o_pattern}"
        }
        expected_recipes = {
            'recipe_c_o_pattern': ["compiler", "extraflag", "myfile"],
            'recipe_cpp_o_pattern': ["compiler", "extraflag", "myfile"],
            'recipe_S_o_pattern': ["compiler", "extraflag", "myfile"],
            'recipe_c_combine_pattern': ["compiler", "extraflag", "myfile"],
            'recipe_ar_pattern': ["compiler", "extraflag", "myfile"]
        }
        recipes = gpb.extract_expanded_recipes(test_platform_def)
        self.assertDictEqual(expected_recipes, recipes)


class ExtractorsTests(unittest.TestCase):
    def test_extract_kv_tokens(self):
        expected_result = set([
            ('TEST_NO_VALUE', None),
            ('TEST', 'VALUE')
        ])
        result = gpb.extract_kv_tokens(
            ["TEST_NO_VALUE", "TEST=VALUE"],
            lambda t: re.search("^([A-Z_]+)=?([A-Z]+)?$", t)
        )
        self.assertEqual(expected_result, result)

    def test_extract_kv_tokens_consumes(self):
        expected_match_result = set([
            ('A', None),
            ('B', 'VALUE')
        ])
        expected_left_tokens = ["C=VALUE"]
        tokens = ["A", "B=VALUE", "B=VALUE", "C=VALUE"]
        result = gpb.extract_kv_tokens(
            tokens,
            lambda t: re.search("^([AB]+)=?([A-Z]+)?$", t)
        )
        self.assertEqual(expected_match_result, result)
        self.assertEqual(expected_left_tokens, tokens)

    def test_extract_v_tokens(self):
        expected_result = set(["A", "B", "C"])
        result = gpb.extract_v_tokens(
            ["opt:A", "opt:B", "opt:C"],
            lambda t: re.search("^opt:([A-Z])$", t)
        )
        self.assertEqual(expected_result, result)

    def test_extract_v_tokens_consumes(self):
        expected_left_tokens = ["A", "B"]
        expected_match_tokens = set("C")
        tokens = ["A", "B", "C", "C", "C"]
        result = gpb.extract_v_tokens(
            tokens, lambda t: re.search("(C)", t), True
        )
        self.assertListEqual(expected_left_tokens, tokens)
        self.assertSetEqual(expected_match_tokens, result)

    def test_extract_cppdefines(self):
        expected_defines = set([
            ('USBCON', None),
            ('USB_MANUFACTURER', '{build.usb_manufacturer}'),
            ('ARDUINO_{build.board}', None)
        ])
        defines = gpb.extract_cppdefines(
            [
                "-DUSBCON",
                "-DUSB_MANUFACTURER={build.usb_manufacturer}",
                "-DARDUINO_{build.board}"
            ]
        )
        self.assertSetEqual(expected_defines, defines)

    def test_extract_cpppath(self):
        expected_cpppaths = set([
            "{build.system.path}",
            "/c/Program Files/mbed-os",
            "."
        ])
        cpppaths = gpb.extract_cpppath(
            ["-I{build.system.path}", "-I/c/Program Files/mbed-os", "-I."]
        )
        self.assertSetEqual(expected_cpppaths, cpppaths)

    def test_extract_libs(self):
        tokens = [
            "test should not be in result",
            "-ldevkit-sdk-core-lib",
            "-lwlan",
            "-lstsafe",
            "-ldevkit-sdk-core-lib",
            "-lm",
            "-lstdc++"
        ]
        expected_libs = set([
            "devkit-sdk-core-lib",
            "wlan",
            "stsafe",
            "devkit-sdk-core-lib",
            "m",
            "stdc++"
        ])
        libs = gpb.extract_libs(tokens)
        self.assertSetEqual(expected_libs, libs)

    def test_extract_libpaths(self):
        expected_libpaths = set([
            ".",
            "libs",
            "/system/libs"
        ])
        libpaths = gpb.extract_libpaths([
            "test should not be in result",
            "-L.",
            "-Llibs",
            "-L/system/libs"
        ])
        self.assertSetEqual(expected_libpaths, libpaths)


class ListSetUtilTests(unittest.TestCase):
    def test_intersection_where_exists(self):
        list1 = [1, 2, 3]
        list2 = [2, 3, 4]
        expected_result = [2, 3]
        result = gpb.intersection(list1, list2)
        self.assertListEqual(expected_result, result)

    def test_intersection_where_not_exist(self):
        list1 = [1, 2, 3]
        list2 = [4, 5, 6]
        expected_result = []
        result = gpb.intersection(list1, list2)
        self.assertListEqual(expected_result, result)

    def test_difference_where_exists(self):
        list1 = [1, 2, 3, 4]
        list2 = [3, 4, 5, 6]
        expected_result = [1, 2]
        result = gpb.difference(list1, list2)
        self.assertListEqual(expected_result, result)

    def test_difference_where_not_exist(self):
        list1 = [1, 2, 3]
        list2 = [1, 2, 3, 4, 5, 6]
        expected_result = []
        result = gpb.difference(list1, list2)
        self.assertListEqual(expected_result, result)


if __name__ == "__main__":
    unittest.main()
