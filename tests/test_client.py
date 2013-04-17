# coding: utf-8
from __future__ import absolute_import, unicode_literals, print_function

import os
from unittest import TestCase

from speicher import Speicher, exceptions


class SpeicherTest(TestCase):

    def setUp(self):
        host = os.environ.get(b'SERVER_HOST', b'localhost')
        port = int(os.environ.get(b'SERVER_PORT', 14567))
        client = self.client = Speicher(host=host, port=port)
        client.reset()
        self.addCleanup(client.close)

    def test_set_get(self):
        self.assertIsNone(self.client.get(b'foo'))
        self.client.set(b'foo', 'bar')
        self.assertEqual('bar', self.client.get(b'foo'))

    def test_set_list(self):
        self.assertIsNone(self.client.get(b'foo'))
        self.client.set(b'foo', ['b', 'a', 'r'])
        self.assertEqual(['b', 'a', 'r'], self.client.get(b'foo'))

    def test_set_none(self):
        self.assertIsNone(self.client.get(b'foo'))
        self.client.set(b'foo', None)
        self.assertFalse(self.client.delete(b'foo'))

    def test_delete(self):
        self.client.set(b'foo', 'bar')
        self.assertEqual('bar', self.client.get(b'foo'))
        self.assertTrue(self.client.delete(b'foo'))
        self.assertIsNone(self.client.get(b'foo'))

    def test_reset(self):
        self.client.set(b'foo', 'bar')
        self.assertEqual('bar', self.client.get(b'foo'))
        self.client.reset()
        self.assertIsNone(self.client.get(b'foo'))

    def test_wrong_command(self):
        with self.assertRaises(exceptions.ClientError):
            self.client._execute(b'UNKNOWN')

    def test_wrong_get_arguments(self):
        with self.assertRaises(exceptions.ClientError):
            self.client._execute(b'GET')

    def test_wrong_set_arguments(self):
        with self.assertRaises(exceptions.ClientError):
            self.client._execute(b'GET', key=b'test')

    def test_wrong_delete_arguments(self):
        with self.assertRaises(exceptions.ClientError):
            self.client._execute(b'DELETE')
