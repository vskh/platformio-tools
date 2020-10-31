# Copyright 2014-present PlatformIO <contact@platformio.org>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
Arduino

Arduino Wiring-based Framework allows writing cross-platform software to
control devices attached to a wide range of Arduino boards to create all
kinds of creative coding, interactive objects, spaces or physical experiences.

http://www.stm32duino.com
"""

from os import walk
from os.path import isdir, join
from typing import Dict, AnyStr, Any

from SCons.Script import DefaultEnvironment

env = DefaultEnvironment()
platform = env.PioPlatform()
board = env.BoardConfig()

FRAMEWORK_DIR = platform.get_package_dir("framework-arduinostm32mxchip")
FRAMEWORK_VERSION = platform.get_package_version(
    "framework-arduinostm32mxchip")
assert isdir(FRAMEWORK_DIR)

env.SConscript("../_bare.py")

COMPILE_OPTS = dict(
    ASFLAGS={ASFLAGS},
    CFLAGS={CFLAGS},
    CCFLAGS={CCFLAGS},
    CXXFLAGS={CXXFLAGS},
    CPPDEFINES={CPPDEFINES},
    LIBPATH={LIBPATH},
    LIBS={LIBS},
    LINKFLAGS={LINKFLAGS},
    LIBSOURCE_DIRS=[join(FRAMEWORK_DIR, "libraries")]
)

BOARD_SUBS = dict(
    build_arch="STM32",
    build_board="MXCHIP_AZ3166",
    build_core_path=join(FRAMEWORK_DIR, "cores", "arduino"),
    build_mcu=board.get("build.cpu"),
    build_path=FRAMEWORK_DIR,
    build_project_name="pio-project",
    build_system_path=join(FRAMEWORK_DIR, "system"),
    build_variant_path=join(FRAMEWORK_DIR, "variants",
                            board.get("build.variant")),
    build_ldscript=board.get(
        "build.ldscript", board.get("build.arduino.ldscript")),
    runtime_ide_version=10813
)

{HELPERS}

env.Append(
    ASFLAGS=COMPILE_OPTS["ASFLAGS"],
    CFLAGS=COMPILE_OPTS["CFLAGS"],
    CCFLAGS=COMPILE_OPTS["CCFLAGS"],
    CXXFLAGS=COMPILE_OPTS["CXXFLAGS"],
    CPPDEFINES=COMPILE_OPTS["CPPDEFINES"],
    LIBPATH=COMPILE_OPTS["LIBPATH"],
    LIBS=COMPILE_OPTS["LIBS"],
    LINKFLAGS=COMPILE_OPTS["LINKFLAGS"],
    LIBSOURCE_DIRS=COMPILE_OPTS["LIBSOURCE_DIRS"]
)

env.Replace(LDSCRIPT_PATH=BOARD_SUBS['build_ldscript'])
