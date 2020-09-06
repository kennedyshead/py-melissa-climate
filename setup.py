#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""A setuptools based setup module.

See:
https://packaging.python.org/en/latest/distributing.html
https://github.com/pypa/sampleproject
"""

# Always prefer setuptools over distutils
from setuptools import setup, find_packages
from os import path

here = path.abspath(path.dirname(__file__))

__author__ = 'Magnus Knutas'
VERSION = '2.1.4'

# Arguments marked as "Required" below must be included for upload to PyPI.
# Fields marked as "Optional" may be commented out.

setup(
    name='py-melissa-climate',
    version=VERSION,
    description='Api wrapper for Melissa Climate http://seemelissa.com',
    setup_requires=['setuptools-markdown'],
    long_description_markdown_filename='README.md',
    url='https://github.com/kennedyshead/py-melissa-climate',
    download_url=
    'https://github.com/kennedyshead/py-melissa-climate/archive/%s.tar.gz' % VERSION,
    author=__author__,
    author_email='magnusknutas@gmail.com',
    license='MIT license',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
    ],
    keywords='Api Melissa development wrapper',
    packages=find_packages(exclude=['contrib', 'docs', 'tests']),
    install_requires=['requests', 'requests-futures', 'aiohttp'],
    test_suite='tests',
    extras_require={
        'dev': ['check-manifest'],
        'test': ['coverage', 'mock'],
    },
)
