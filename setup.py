"""prawcore setup.py."""

import re
from codecs import open
from os import path
from setuptools import setup


PACKAGE_NAME = 'prawcore'
HERE = path.abspath(path.dirname(__file__))
with open(path.join(HERE, 'README.rst'), encoding='utf-8') as fp:
    README = fp.read()
with open(path.join(HERE, PACKAGE_NAME, 'const.py'),
          encoding='utf-8') as fp:
    VERSION = re.search("__version__ = '([^']+)'", fp.read()).group(1)


setup(name=PACKAGE_NAME,
      author='Bryce Boe',
      author_email='bbzbryce@gmail.com',
      classifiers=[
          'Development Status :: 4 - Beta',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: BSD License',
          'Natural Language :: English',
          'Programming Language :: Python',
          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3.3',
          'Programming Language :: Python :: 3.4',
          'Programming Language :: Python :: 3.5',
          'Programming Language :: Python :: Implementation :: CPython'],
      dependency_links=[
          ('https://github.com/sigmavirus24/betamax_matchers/tarball/master'
           '#egg=betamax_matchers-0.3.0')
      ],
      description='Low-level communication layer for PRAW 4+.',
      install_requires=['requests >=2.9.1, <3.0'],
      keywords='praw reddit api',
      license='Simplified BSD License',
      long_description=README,
      packages=[PACKAGE_NAME],
      tests_require=['betamax >=0.8, <0.9',
                     'betamax_matchers >=0.3.0, <0.4',
                     'betamax-serializers >=0.2.0, <0.3',
                     'mock ==1.0.1'],
      test_suite='tests',
      url='https://github.com/praw-dev/prawcore',
      version=VERSION)
