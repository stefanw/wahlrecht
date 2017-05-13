#!/usr/bin/env python

import codecs
import re
import os

from setuptools import setup, find_packages


def read(*parts):
    filename = os.path.join(os.path.dirname(__file__), *parts)
    with codecs.open(filename, encoding='utf-8') as fp:
        return fp.read()


def find_version(*file_paths):
    version_file = read(*file_paths)
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")


setup(
    name="wahlrecht",
    version=find_version('wahlrecht', '__init__.py'),
    url='https://github.com/stefanw/wahlrecht',
    license='MIT',
    description="Python module to download and parse wahlrecht.de polls",
    long_description=read('README.md'),
    author='Stefan Wehrmeyer',
    author_email='mail@stefanwehrmeyer.com',
    packages=find_packages(exclude=['tests']),
    install_requires=[
        'requests',
        'lxml'
    ],
    test_suite="tests",
    include_package_data=True,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Scientific/Engineering'
    ]
)
