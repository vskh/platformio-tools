#!/usr/bin/env python3

import unittest
import re
import generate_pio_build as gpb


class ReadPlatformDefTests(unittest.TestCase):
    def test_expands_dots_in_format_placeholders(self):
        platform_def = gpb.read_platform_def("platform_test.txt")

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


class ExtractExpandedRecipesTests(unittest.TestCase):
    test_platform_def = {
        'test1': "gcc",
        'test2': "g++",
        'test3': "as",
        'test4': "ld",
        'test5': "ar",
        'recipe.c.o.pattern': "{test1} myfile",
        'recipe.cpp.o.pattern': "{test2} myfile",
        'recipe.S.o.pattern': "{test3} myfile",
        'recipe.c.combine.pattern': "{test4} myfile",
        'recipe.ar.pattern': "{test5} myfile"
    }

    def test_works(self):
        expected_recipes = {
            'recipe.c.o.pattern': ["gcc", "myfile"],
            'recipe.cpp.o.pattern': ["g++", "myfile"],
            'recipe.S.o.pattern': ["as", "myfile"],
            'recipe.c.combine.pattern': ["ld", "myfile"],
            'recipe.ar.pattern': ["ar", "myfile"]
        }
        recipes = gpb.extract_expanded_recipes(self.test_platform_def)
        self.assertDictEqual(recipes, expected_recipes)


class ExtractorsTests(unittest.TestCase):
    def test_extract_kv_tokens(self):
        expected_result = {
            'TEST_NO_VALUE': None,
            'TEST': 'VALUE'
        }
        result = gpb.extract_kv_tokens(
            ["TEST_NO_VALUE", "TEST=VALUE"], lambda t: re.search("^([A-Z_]+)=?([A-Z]+)?$", t))
        self.assertEqual(result, expected_result)

    def test_extract_v_tokens(self):
        expected_result = ["A", "B", "C"]
        result = gpb.extract_v_tokens(
            ["opt:A", "opt:B", "opt:C"], lambda t: re.search("^opt:([A-Z])$", t))
        self.assertEqual(result, expected_result)

    def test_extract_cppdefines(self):
        expected_defines = {
            'USBCON': None,
            'USB_MANUFACTURER': '{build.usb_manufacturer}'
        }
        defines = gpb.extract_cppdefines(
            ["-DUSBCON", "-DUSB_MANUFACTURER={build.usb_manufacturer}"])
        self.assertDictEqual(defines, expected_defines)

    def test_extract_cpppath(self):
        expected_cpppaths = [
            "{build.system.path}",
            "/c/Program Files/mbed-os",
            "."
        ]
        cpppaths = gpb.extract_cpppath(
            ["-I{build.system.path}", "-I/c/Program Files/mbed-os", "-I."])
        self.assertListEqual(cpppaths, expected_cpppaths)

    def test_extract_libs(self):
        expected_libs = [
            "devkit-sdk-core-lib",
            "wlan",
            "stsafe",
            "devkit-sdk-core-lib",
            "m",
            "stdc++"
        ]
        libs = gpb.extract_libs([
            "test should not be in result",
            "-ldevkit-sdk-core-lib",
            "-lwlan",
            "-lstsafe",
            "-ldevkit-sdk-core-lib",
            "-lm",
            "-lstdc++"
        ])
        self.assertListEqual(libs, expected_libs)


if __name__ == "__main__":
    unittest.main()
