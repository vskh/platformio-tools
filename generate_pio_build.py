#!/usr/bin/env python3

"""
PlatformIO template build script generator using Arduino IDE 3rd-party hardware
specification file (platform.txt).
"""

from pprint import pformat
import sys
import re
import shlex
import inspect
from typing import Dict, List, Set, Tuple, Callable, AnyStr, Any

RECIPE_IDS = {
    'c': 'recipe_c_o_pattern',          # C compiling
    'c++': 'recipe_cpp_o_pattern',      # C++ compiling
    'as': 'recipe_S_o_pattern',         # asm compiling
    'ld': 'recipe_c_combine_pattern',   # linking
    'ar': 'recipe_ar_pattern'           # creating archive
}


def intersection(list1: List[AnyStr], list2: List[AnyStr]) -> List[AnyStr]:
    return [item for item in list1 if item in list2]


def difference(list1: List[AnyStr], list2: List[AnyStr]) -> List[AnyStr]:
    return [item for item in list1 if item not in list2]


def prepare_for_shell(s: AnyStr) -> AnyStr:
    s = re.sub("\(", "\\(", s)
    s = re.sub("\)", "\\)", s)
    return s


def extract_v_tokens(tokens: List[AnyStr], match: Callable[[AnyStr], re.Match], consume=False) -> Set[AnyStr]:
    result = set()
    to_clean = set()
    for token in tokens:
        m = match(token)
        if m is not None:
            to_clean.add(token)
            v = m.group(1)
            result.add(prepare_for_shell(v))
    if consume:
        for token in to_clean:
            while True:  # to remove all occurrences
                try:
                    tokens.remove(token)
                except:
                    break

    return result


def extract_kv_tokens(tokens: List[AnyStr], match: Callable[[AnyStr], re.Match], consume=True) -> Set[Tuple[AnyStr, AnyStr]]:
    result = set()
    to_clean = []
    for token in tokens:
        matches = match(token)
        if matches is not None:
            to_clean.append(token)
            k, v = matches.groups()
            result.add((k, prepare_for_shell(v) if v else None))
    if consume:
        for token in to_clean:
            while True:
                try:
                    tokens.remove(token)
                except:
                    break
    return result


def extract_defines(tokens: List[AnyStr]) -> Set[Tuple[AnyStr, AnyStr]]:
    return extract_kv_tokens(
        tokens, lambda t: re.search("^-D([\w\{\}\.]+)(?:=(.*?)?)?$", t), True
    )


def extract_includes(tokens: List[AnyStr]) -> Set[AnyStr]:
    return extract_v_tokens(tokens, lambda t: re.search("^-I(.*?)$", t), True)


def extract_cppdefines(tokens: List[AnyStr]) -> Set[Tuple[AnyStr, AnyStr]]:
    return extract_defines(tokens)


def extract_cpppath(tokens: List[AnyStr]) -> Set[AnyStr]:
    return extract_includes(tokens)


def extract_libs(tokens: List[AnyStr]) -> Set[AnyStr]:
    return extract_v_tokens(tokens, lambda t: re.search("^-l(.*?)$", t), True)


def extract_libpaths(tokens: List[AnyStr]) -> Set[AnyStr]:
    return extract_v_tokens(tokens, lambda t: re.search("^-L(.*?)$", t), True)


def extract_build_flags(recipes: Dict[AnyStr, List[AnyStr]]) -> Dict[AnyStr, Any]:
    extracted_flags = {
        'ASFLAGS': list(),       # assembler flags
        'CCFLAGS': list(),       # C/C++ common compiler flags
        'CFLAGS': list(),        # C compiler flags
        'CPPDEFINES': list(),    # C preprocessor flags
        'CPPPATH': list(),       # C preprocessor includes search path
        'CXXFLAGS': list(),      # C++ compiler flags
        'LIBPATH': list(),       # library search path
        'LIBS': list(),          # libraries to link with
        'LINKFLAGS': list()      # linker flags
    }

    # process AS flags
    as_recipe = recipes[RECIPE_IDS['as']]
    extracted_flags['ASFLAGS'].extend(as_recipe)

    # process C flags
    c_recipe = recipes[RECIPE_IDS['c']]
    extracted_flags['CPPDEFINES'].extend(extract_cppdefines(c_recipe))
    extracted_flags['CPPPATH'].extend(extract_cpppath(c_recipe))

    # process C++ flags
    cxx_recipe = recipes[RECIPE_IDS['c++']]
    extracted_flags['CPPDEFINES'].extend(extract_cppdefines(cxx_recipe))
    extracted_flags['CPPPATH'].extend(extract_cpppath(cxx_recipe))

    # extract shared C/C++ flags
    extracted_flags['CCFLAGS'].extend(intersection(c_recipe, cxx_recipe))
    extracted_flags['CFLAGS'].extend(difference(c_recipe, cxx_recipe))
    extracted_flags['CXXFLAGS'].extend(difference(cxx_recipe, c_recipe))

    # collect libraries
    ld_recipe = recipes[RECIPE_IDS['ld']]
    extracted_flags['LIBS'].extend(extract_libs(ld_recipe))
    extracted_flags['LIBPATH'].extend(extract_libpaths(ld_recipe))
    extracted_flags['LINKFLAGS'].extend(ld_recipe)

    extracted_flags['CPPDEFINES'] = list(set(extracted_flags['CPPDEFINES']))
    extracted_flags['CPPPATH'] = list(set(extracted_flags['CPPPATH']))

    return extracted_flags


def expand(def_str: AnyStr, def_index: Dict[AnyStr, AnyStr]) -> AnyStr:
    class fmt_dict(dict):
        def __missing__(self, key):
            return f"{{{key}}}"

    if not def_str:
        return None

    substitutions = fmt_dict(def_index)
    before_expansion = def_str
    after_expansion = def_str.format_map(substitutions)
    while before_expansion != after_expansion:
        before_expansion = after_expansion
        after_expansion = after_expansion.format_map(substitutions)

    return after_expansion


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


def clean_recipe(recipe: List[AnyStr]) -> List[AnyStr]:
    # pop first element containing command
    recipe.pop(0)

    # remove any output spec
    if "-o" in recipe:
        output_opt = recipe.index("-o")
        recipe = recipe[0:output_opt] + recipe[output_opt + 2:]

    # filter tokens
    to_clean = ["{includes}", "{object_files}", "{source_file}"]
    recipe = [token for token in recipe if token not in to_clean]

    return recipe


def clean_recipes(recipes: Dict[AnyStr, List[AnyStr]]) -> Dict[AnyStr, List[AnyStr]]:
    result = dict()
    for rid, recipe in recipes.items():
        result[rid] = clean_recipe(recipe)
    return result


def expand_dict(d: Dict[AnyStr, Any], subs: Dict[AnyStr, AnyStr]) -> Dict[AnyStr, Any]:
    result = dict()
    for key, val in d.items():
        key = expand(key, subs)

        if isinstance(val, str):
            result[key] = expand(val, subs)
        elif isinstance(val, tuple):
            result[key] = tuple(expand(token, subs) for token in val)
        elif isinstance(val, list):
            result[key] = list()
            for token in val:
                if isinstance(token, tuple):
                    result[key].append(tuple(expand(el, subs) for el in token))
                else:
                    result[key].append(expand(token, subs))

    return result


def main(argv):
    num_args = len(argv)

    if num_args < 3 or num_args > 4:
        print("Usage: {} <platform.txt> <build_script_template> [<output_file>]".format(
            argv[0]))
        exit(1)

    platform = argv[1]
    template_path = argv[2]

    if num_args == 4:
        output_path = argv[3]
    else:
        output_path = None

    platform_def = read_platform_def(platform)
    recipes = extract_expanded_recipes(platform_def)
    recipes = clean_recipes(recipes)
    substitutions = extract_build_flags(recipes)
    substitutions['HELPERS'] = "\n".join([
        inspect.getsource(expand),
        inspect.getsource(expand_dict),
        """
COMPILE_OPTS = expand_dict(COMPILE_OPTS, BOARD_SUBS)
"""
    ])

    with open(template_path, "r") as template:
        script_content = template.read()

    script_content = expand(script_content, substitutions)

    if output_path:
        with open(output_path, "w") as output:
            output.write(script_content)
    else:
        print(script_content)


if __name__ == "__main__":
    main(sys.argv)
