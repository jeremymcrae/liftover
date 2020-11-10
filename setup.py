
import io
from setuptools import setup
import sys
from distutils.core import Extension
from Cython.Build import cythonize

EXTRA_COMPILE_ARGS = ['-std=c++11']
EXTRA_LINK_ARGS = []
if sys.platform == "darwin":
    EXTRA_COMPILE_ARGS += ["-stdlib=libc++", "-mmacosx-version-min=10.9"]
    EXTRA_LINK_ARGS += ["-stdlib=libc++", "-mmacosx-version-min=10.9"]

lifter = cythonize([
    Extension('liftover.chain_file',
        extra_compile_args=EXTRA_COMPILE_ARGS,
        extra_link_args=EXTRA_LINK_ARGS,
        sources=['liftover/chain_file.pyx',
            'src/gzstream/gzstream.C',
            'src/chain.cpp',
            'src/utils.cpp',
            'src/headers.cpp',
            'src/target.cpp',
            'src/chain_file.cpp'],
        include_dirs=['src/', 'src/gzstream/', 'src/intervaltree/'],
        library_dirs=['src/', 'src/gzstream/', 'src/intervaltree/'],
        libraries=['z'],
        language='c++'),
    ])

setup(name='liftover',
    description='Package for converting between genome build coordinates',
    long_description=io.open('README.md', encoding='utf-8').read(),
    long_description_content_type='text/markdown',
    version='1.1.6',
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
