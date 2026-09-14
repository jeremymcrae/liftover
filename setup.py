
import glob
import os
import sys

from setuptools import setup, Extension
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

sources = [
    'src/liftover/chain_file.pyx',
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
      )
