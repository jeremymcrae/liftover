
import glob
import os
import sys

from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext
from Cython.Build import cythonize

EXTRA_COMPILE_ARGS = []
EXTRA_LINK_ARGS = []
if sys.platform == "win32":
    EXTRA_COMPILE_ARGS += ['/std:c++14']
else:
    EXTRA_COMPILE_ARGS += ['-std=c++11']
    if sys.platform == "darwin":
        EXTRA_COMPILE_ARGS += ["-stdlib=libc++"]
        EXTRA_LINK_ARGS += ["-stdlib=libc++"]
        sdk_base = "/Library/Developer/CommandLineTools/SDKs/MacOSX.sdk"
        if os.path.exists(sdk_base):
            EXTRA_COMPILE_ARGS += [
                f"-I{sdk_base}/usr/include/c++/v1",
                f"-I{sdk_base}/usr/include",
            ]
            EXTRA_LINK_ARGS += [
                f"-L{sdk_base}/usr/lib",
            ]

class BuildExt(build_ext):
    ''' Custom build_ext to prepare gzstream without mutating tracked sources.

    gzstream.C includes <gzstream.h>, which fails on macOS clang if src/gzstream
    is in include_dirs because clang confuses src/gzstream/version with the
    standard library <version> header. Additionally, Windows compilers do not
    recognize the .C extension as C++.

    We generate a temporary gzstream.cpp in the build directory with the header
    path adjusted, leaving the tracked submodule completely untouched.
    '''
    def build_extension(self, ext):
        os.makedirs(self.build_temp, exist_ok=True)
        dest_cpp = os.path.join(self.build_temp, 'gzstream.cpp')
        src_c = os.path.join('src', 'gzstream', 'gzstream.C')

        with open(src_c, 'rt') as f:
            content = f.read()

        content = content.replace('#include <gzstream.h>', '#include "gzstream/gzstream.h"')

        with open(dest_cpp, 'wt') as f:
            f.write(content)

        ext.sources = [dest_cpp if s == src_c else s for s in ext.sources]
        super().build_extension(ext)

sources = [
    'src/liftover/chain_file.pyx',
    'src/gzstream/gzstream.C',
    'src/chain.cpp',
    'src/utils.cpp',
    'src/headers.cpp',
    'src/target.cpp',
    'src/chain_file.cpp',
]

libs = ['z']
include_dirs = ['src/', 'src/intervaltree/']

if sys.platform == 'win32':
    sources += glob.glob('src/zlib/*.c')
    include_dirs.append('src/zlib/')
    libs = []

ext = [
    Extension('liftover.chain_file',
              extra_compile_args=EXTRA_COMPILE_ARGS,
              extra_link_args=EXTRA_LINK_ARGS,
              sources=sources,
              include_dirs=include_dirs,
              library_dirs=['src/', 'src/intervaltree/'],
              libraries=libs,
              language='c++'),
    ]

setup(package_dir={'': 'src'},
      ext_modules=cythonize(ext),
      cmdclass={'build_ext': BuildExt},
      )
