
from setuptools import setup

setup(name='liftover',
    description='Package for converting between genome build coordinates',
    version='1.0.0',
    author='Jeremy McRae',
    author_email='jmcrae@illumina.com',
    url='https://github.com/jeremy_mcrae/liftover',
    packages=['liftover'],
    install_requires=['intervaltree',
        'requests',
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Topic :: Scientific/Engineering :: Bio-Informatics',
    ])
