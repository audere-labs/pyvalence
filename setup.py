#!/usr/bin/env python

import os
from setuptools import setup
from pyvalence import __version__
from os import path

PKG_NAME = 'pyvalence'
PKG_AUTHOR = 'Audere Labs'
PKG_LICENSE = 'BSD'

AUTHOR_EMAIL = 'audere.labs@gmail.com'
MAINTAINER_EMAIL = ''  # google group / forum

URL = 'https://audere.github.com/valence'
DOWNLOAD_URL = ''

DESCRIPTION = 'Package for processing analytical chemistry data.'

# Get the long description from the README file
here = path.abspath(path.dirname(__file__))
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    LONG_DESCRIPTION = f.read()



options = {
    'version': __version__,
    'name': PKG_NAME,
    'author': PKG_AUTHOR,
    'license': PKG_LICENSE,
    'author_email': AUTHOR_EMAIL,
    'maintainer_email': MAINTAINER_EMAIL,
    'url': URL,
    'download_url': DOWNLOAD_URL,
    'description': DESCRIPTION,
    'long_description': LONG_DESCRIPTION,
    'platforms': ['Any'],
    'classifiers': [
        'Development Status :: 1 - Planning',
        'Environment :: Console',
        'Intended Audience :: Science/Research',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Scientific/Engineering :: Chemistry'
    ],
    'packages': [
        'pyvalence', 'pyvalence.build', 'pyvalence.analyze'
    ],
    'package_data': {'pyvalence': []},
    'include_package_data': True,
    'install_requires': ['numpy', 'scipy', 'pandas']
}

setup(**options)
