
import glob
import sys

from setuptools import setup, Extension
from Cython.Build import cythonize

EXTRA_COMPILE_ARGS = []
EXTRA_LINK_ARGS = []
if sys.platform == "win32":
    EXTRA_COMPILE_ARGS += ['/std:c++14', '/O2']
else:
    EXTRA_COMPILE_ARGS += ['-std=c++11', '-O2']
    if sys.platform == "darwin":
        EXTRA_COMPILE_ARGS += ["-stdlib=libc++"]
        EXTRA_LINK_ARGS += ["-stdlib=libc++"]

sources = [
    'src/liftover/chain_file.pyx',
    'src/chain.cpp',
    'src/headers.cpp',
    'src/target.cpp',
    'src/chain_file.cpp',
]

libs = ['z']
include_dirs = ['src/']

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
              libraries=libs,
              language='c++'),
    ]

setup(
    ext_modules=cythonize(ext),
)
