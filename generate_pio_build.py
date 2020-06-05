#!/usr/bin/env python3

"""
PlatformIO template build script generator using Arduino IDE 3rd-party hardware
specification file (platform.txt).
"""

import sys
import re
from typing import Dict


def expand(def_str: str, def_index: Dict[str, str]) -> str:
    class fmt_dict(dict):
        def __missing__(self, key):
            return f"{{{key}}}"

    return def_str.format_map(fmt_dict(def_index))


def extract_expanded_recipes(platform_def: Dict[str, str]) -> Dict[str, str]:
    recipes = ['recipe.c.o.pattern',        # C compiling
               'recipe.cpp.o.pattern',      # C++ compiling
               'recipe.S.o.pattern',        # asm compiling
               'recipe.c.combine.pattern',  # linking
               'recipe.ar.pattern']         # creating archive


def read_platform_def(platform_def_path: str) -> Dict[str, str]:
    result = {}
    with open(platform_def_path) as platform:
        for l in platform:
            l = l.strip()

            if not l:
                continue

            if l.startswith("#"):
                continue

            k, v = l.split("=", 1)

            result[k] = v

    return result


def main(argv):
    num_args = len(argv)

    if num_args < 2 or num_args > 3:
        print("Usage: {} <platform.txt> [<output_build_script.py>]".format(
            argv[0]))
        exit(1)

    platform = argv[1]

    if num_args == 3:
        script = argv[2]
    else:
        script = None

    platform_def = read_platform_def(platform)

    print(platform_def)


if __name__ == "__main__":
    main(sys.argv)
