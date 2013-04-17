#!/usr/bin/env python
# coding: utf-8
import os
import re
import sys

from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand


install_requires = [
    'six>=1.3.0',
    'anyjson>=0.3.0',
]

tests_require=[
    'tox',
]


# Description, version and other meta information.

re_meta = re.compile(r'__(\w+?)__\s*=\s*(.*)')
re_vers = re.compile(r'VERSION\s*=\s*\((.*?)\)')
re_doc = re.compile(r'^"""(.+?)"""')
rq = lambda s: s.strip("\"'")


def add_default(m):
    attr_name, attr_value = m.groups()
    return ((attr_name, rq(attr_value)),)


def add_version(m):
    v = list(map(rq, m.groups()[0].split(', ')))
    return (('VERSION', '.'.join(v[0:3]) + ''.join(v[3:])),)


def add_doc(m):
    return (('doc', m.groups()[0]),)

pats = {re_meta: add_default,
        re_vers: add_version,
        re_doc: add_doc}
here = os.path.abspath(os.path.dirname(__file__))
meta_fh = open(os.path.join(here, 'speicher/__init__.py'))
try:
    meta = {}
    for line in meta_fh:
        if line.strip() == '# -eof meta-':
            break
        for pattern, handler in pats.items():
            m = pattern.match(line.strip())
            if m:
                meta.update(handler(m))
finally:
    meta_fh.close()

with open(os.path.join(here, 'README.rst')) as f:
    README = f.read()


class Tox(TestCommand):

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        import tox
        errno = tox.cmdline(self.test_args)
        sys.exit(errno)


setup(
    name='speicher',
    version=meta['VERSION'],
    description=meta['doc'],
    author=meta['author'],
    author_email=meta['contact'],
    url=meta['homepage'],
    long_description=README,
    packages=find_packages(),
    zip_safe=False,
    install_requires=install_requires,
    tests_require=['tox'],
    cmdclass={'test': Tox},
    license='MIT',
    include_package_data=True,
    classifiers=[
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Topic :: Software Development',
    ],
)
