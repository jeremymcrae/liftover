
import io
import glob
import os
import sys

from distutils.ccompiler import new_compiler
from setuptools import setup, Extension
from Cython.Build import cythonize

EXTRA_COMPILE_ARGS = ['-std=c++11']
EXTRA_LINK_ARGS = []
if sys.platform == "darwin":
    EXTRA_COMPILE_ARGS += ["-stdlib=libc++", "-mmacosx-version-min=10.9"]
    EXTRA_LINK_ARGS += ["-stdlib=libc++", "-mmacosx-version-min=10.9"]

def build_zlib():
    ''' compile zlib code to object files for linking with liftover on windows
    
    Returns:
        list of paths to compiled object code
    '''
    include_dirs = ['src/zlib/']
    sources = list(glob.glob('src/zlib/*.c'))
    extra_compile_args = []
    
    cc = new_compiler()
    return cc.compile(sources, include_dirs=include_dirs,
        extra_preargs=extra_compile_args)

def get_gzstream_path():
    ''' workaround for building gzstream on windows

    cython on windows didn't like the .C extension for gzstream. This just
    renames the file (on windows only), and returns the relative path.
    '''
    gzstream_path = 'src/gzstream/gzstream.C'
    if sys.platform == 'win32':
        gzstream_win_path = 'src/gzstream/gzstream.cpp'
        try:
            os.rename(gzstream_path, gzstream_win_path)
        except FileNotFoundError:
            pass  # avoid error on github actions
        gzstream_path = gzstream_win_path
    return gzstream_path

if sys.platform == 'win32':
    zlib, libs = build_zlib(), []
else:
    zlib, libs = [], ['z']

lifter = cythonize([
    Extension('liftover.chain_file',
              extra_compile_args=EXTRA_COMPILE_ARGS,
              extra_link_args=EXTRA_LINK_ARGS,
              sources=['liftover/chain_file.pyx',
                        get_gzstream_path(),
                       'src/chain.cpp',
                       'src/utils.cpp',
                       'src/headers.cpp',
                       'src/target.cpp',
                       'src/chain_file.cpp'],
              extra_objects=zlib,
              include_dirs=['src/', 'src/gzstream/', 'src/intervaltree/', 'src/zlib/'],
              library_dirs=['src/', 'src/gzstream/', 'src/intervaltree/'],
              libraries=libs,
              language='c++'),
    ])

setup(name='liftover',
      description='Package for converting between genome build coordinates',
      long_description=io.open('README.md', encoding='utf-8').read(),
      long_description_content_type='text/markdown',
      version='1.1.11',
      author='Jeremy McRae',
      author_email='jmcrae@illumina.com',
      url='https://github.com/jeremymcrae/liftover',
      packages=['liftover'],
      install_requires=[
          'requests',
      ],
      classifiers=[
          'Development Status :: 4 - Beta',
          'Topic :: Scientific/Engineering :: Bio-Informatics',
      ],
      ext_modules=lifter,
      test_suite='tests',
      )
