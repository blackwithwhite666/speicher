# coding: utf-8
"""Simple client to key-value storage."""
from __future__ import absolute_import, unicode_literals, print_function

VERSION = (0, 1, 0)

__version__ = '.'.join(map(str, VERSION[0:3]))
__author__ = 'Lipin Dmitriy'
__contact__ = 'blackwithwhite666@gmail.com'
__homepage__ = 'https://github.com/blackwithwhite666/speicher'
__docformat__ = 'restructuredtext'

# -eof meta-

from .client import Speicher
