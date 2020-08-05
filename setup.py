"""prawcore setup.py."""

import re
from codecs import open
from os import path
from setuptools import setup


PACKAGE_NAME = "prawcore"
HERE = path.abspath(path.dirname(__file__))
with open(path.join(HERE, "README.rst"), encoding="utf-8") as fp:
    README = fp.read()
with open(path.join(HERE, PACKAGE_NAME, "const.py"), encoding="utf-8") as fp:
    VERSION = re.search('__version__ = "([^"]+)"', fp.read()).group(1)

extras = {
    "ci": ["coveralls"],
    "lint": ["black", "flake8", "pre-commit", "pydocstyle"],
    "test": [
        "betamax >=0.8, <0.9",
        "betamax_matchers >=0.4.0, <0.5",
        "betamax-serializers >=0.2.0, <0.3",
        "mock >=0.8",
        "pytest",
        "testfixtures >4.13.2, <7",
    ],
}
extras["dev"] = extras["lint"] + extras["test"]

setup(
    name=PACKAGE_NAME,
    author="Bryce Boe",
    author_email="bbzbryce@gmail.com",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Natural Language :: English",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    description="Low-level communication layer for PRAW 4+.",
    extras_require=extras,
    install_requires=["requests >=2.6.0, <3.0"],
    python_requires=">=3.5",
    keywords="praw reddit api",
    license="Simplified BSD License",
    long_description=README,
    packages=[PACKAGE_NAME],
    url="https://github.com/praw-dev/prawcore",
    version=VERSION,
)
