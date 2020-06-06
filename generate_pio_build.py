#!/usr/bin/env python3

"""
PlatformIO template build script generator using Arduino IDE 3rd-party hardware
specification file (platform.txt).
"""

import sys
import re
import shlex
from typing import List, Dict, Callable, AnyStr, Any

RECIPE_IDS = {
    'c': 'recipe.c.o.pattern',          # C compiling
    'c++': 'recipe.cpp.o.pattern',      # C++ compiling
    'as': 'recipe.S.o.pattern',         # asm compiling
    'ld': 'recipe.c.combine.pattern',   # linking
    'ar': 'recipe.ar.pattern'           # creating archive
}


def extract_v_tokens(tokens: List[AnyStr], match: Callable[[AnyStr], re.Match]) -> List[AnyStr]:
    result = []
    for token in tokens:
        m = match(token)
        if m is not None:
            v = m.group(1)
            result.append(v)
    return result


def extract_kv_tokens(tokens: List[AnyStr], match: Callable[[AnyStr], re.Match]) -> Dict[AnyStr, AnyStr]:
    result = {}
    for token in tokens:
        matches = match(token)
        if matches is not None:
            k, v = matches.groups()
            result[k] = v if v else None
    return result


def extract_cppdefines(tokens: List[AnyStr]) -> Dict[AnyStr, AnyStr]:
    return extract_kv_tokens(tokens, lambda t: re.search("^-D(\w+)=?(.*?)?$", t))


def extract_cpppath(tokens: List[AnyStr]) -> List[AnyStr]:
    return extract_v_tokens(tokens, lambda t: re.search("^-I(.*?)$", t))


def extract_libs(cmdline: AnyStr) -> List[AnyStr]:
    return extract_v_tokens(cmdline, lambda t: re.search("^-l(.*?)$", t))


def extract_build_flags(recipes: Dict[AnyStr, List[AnyStr]]) -> Dict[AnyStr, Any]:
    extracted_flags = {
        'CCFLAGS': set(),       # C/C++ common compiler flags
        'CFLAGS': set(),        # C compiler flags
        'CPPDEFINES': set(),    # C preprocessor flags
        'CPPPATH': set(),       # C preprocessor includes search path
        'CXXFLAGS': set(),      # C++ compiler flags
        'LIBPATH': set(),       # library search path
        'LIBS': set(),          # libraries to link with
        'LINKFLAGS': set()      # linker flags
    }

    # collect C flags
    c_recipe = recipes[RECIPE_IDS['c']]
    extracted_flags['CPPDEFINES'].add(extract_cppdefines(c_recipe))
    extracted_flags['CPPPATH'].add(extract_cpppath(c_recipe))

    # collect C++ flags
    cxx_recipe = recipes[RECIPE_IDS['c++']]
    extracted_flags['CPPDEFINES'].add(extract_cppdefines(cxx_recipe))
    extracted_flags['CPPPATH'].add(extract_cpppath(cxx_recipe))

    # collect libraries
    ld_recipe = recipes[RECIPE_IDS['ld']]
    extracted_flags['LIBS'].add(extract_libs(ld_recipe))
    extracted_flags['LINKFLAGS'].add()

    return extracted_flags


def expand(def_str: AnyStr, def_index: Dict[AnyStr, AnyStr]) -> AnyStr:
    class fmt_dict(dict):
        def __missing__(self, key):
            return f"{{{key}}}"

    return def_str.format_map(fmt_dict(def_index))


def extract_expanded_recipes(platform_def: Dict[AnyStr, AnyStr]) -> Dict[AnyStr, List[AnyStr]]:
    result = {}
    recipes = RECIPE_IDS.values()
    for recipe in recipes:
        expanded_recipe = expand(platform_def[recipe], platform_def)
        result[recipe] = shlex.split(expanded_recipe)

    return result


def read_platform_def(platform_def_path: AnyStr) -> Dict[AnyStr, AnyStr]:
    result = {}
    with open(platform_def_path) as platform:
        for l in platform:
            l = l.strip()

            if not l:
                continue

            if l.startswith("#"):
                continue

            k, v = l.split("=", 1)

            def dot_filter(m): return m.group(0).replace(".", "_")

            result[k.replace(".", "_")] = re.sub("\{[^{}]+\}", dot_filter, v)

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
    recipes = extract_expanded_recipes(platform_def)
    build_flags = extract_build_flags(recipes)
    print(build_flags)


if __name__ == "__main__":
    main(sys.argv)
