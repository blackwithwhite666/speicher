# coding: utf-8
from __future__ import absolute_import, unicode_literals, print_function

from .base import TestCase
from .relay import FramedRelay

from ..client import Speicher
from ..exceptions import ServerError, MalformedReply


class ClientTest(TestCase):

    def create_relay(self, **kwargs):
        relay = self.relay = FramedRelay(**kwargs)
        self.addCleanup(relay.stop)
        relay.start()
        return (relay.host, relay.port)

    def create_client(self, callback=None, **kwargs):
        host, port = self.create_relay(callback=callback)
        client = Speicher(host=host, port=port, **kwargs)
        self.addCleanup(client.close)
        return client

    def test_key(self):
        def inner_cb(data):
            return {b'status_code': 200, b'value': 'bar'}
        client = self.create_client(inner_cb)
        with self.assertRaises(ValueError):
            client.get('')
        with self.assertRaises(TypeError):
            client.get(object())

    def test_malformed_reply(self):
        def inner_cb(data):
            return {}
        client = self.create_client(inner_cb)
        with self.assertRaises(MalformedReply):
            client.get('foo')

    def test_bad_reply(self):
        def inner_cb(data):
            return None
        client = self.create_client(inner_cb)
        with self.assertRaises(MalformedReply):
            client.get('foo')

    def test_unknown_code(self):
        def inner_cb(data):
            return {b'status_code': 100}
        client = self.create_client(inner_cb)
        with self.assertRaises(MalformedReply):
            client.get('foo')

    def test_server_error(self):
        def inner_cb(data):
            return {b'status_code': 503}
        client = self.create_client(inner_cb)
        with self.assertRaises(ServerError):
            client.get('foo')

    def test_get(self):
        def inner_cb(data):
            self.assertEqual(b'GET', data[b'command'])
            self.assertEqual(b'foo', data[b'key'])
            return {b'status_code': 200, b'value': 'bar'}
        client = self.create_client(inner_cb)
        self.assertEqual('bar', client.get('foo'))

    def test_get_not_exist(self):
        def inner_cb(data):
            self.assertEqual(b'GET', data[b'command'])
            self.assertEqual(b'foo', data[b'key'])
            return {b'status_code': 404}
        client = self.create_client(inner_cb)
        self.assertIsNone(client.get('foo'))

    def test_get_malformed(self):
        def inner_cb(data):
            self.assertEqual(b'GET', data[b'command'])
            self.assertEqual(b'foo', data[b'key'])
            return {b'status_code': 200}
        client = self.create_client(inner_cb)
        with self.assertRaises(MalformedReply):
            client.get('foo')

    def test_set(self):
        def inner_cb(data):
            self.assertEqual(b'SET', data[b'command'])
            self.assertEqual(b'foo', data[b'key'])
            self.assertEqual('bar', data[b'value'])
            return {b'status_code': 200}
        client = self.create_client(inner_cb)
        self.assertIsNone(client.set('foo', 'bar'))

    def test_set_none(self):
        def inner_cb(data):
            self.assertEqual(b'DEL', data[b'command'])
            self.assertEqual(b'foo', data[b'key'])
            return {b'status_code': 200}
        client = self.create_client(inner_cb)
        self.assertIsNone(client.set('foo', None))

    def test_delete(self):
        def inner_cb(data):
            self.assertEqual(b'DEL', data[b'command'])
            self.assertEqual(b'foo', data[b'key'])
            return {b'status_code': 200}
        client = self.create_client(inner_cb)
        self.assertTrue(client.delete('foo'))

    def test_delete_not_exist(self):
        def inner_cb(data):
            self.assertEqual(b'DEL', data[b'command'])
            self.assertEqual(b'foo', data[b'key'])
            return {b'status_code': 404}
        client = self.create_client(inner_cb)
        self.assertFalse(client.delete('foo'))

    def test_reset(self):
        def inner_cb(data):
            self.assertEqual(b'RST', data[b'command'])
            return {b'status_code': 200}
        client = self.create_client(inner_cb)
        self.assertIsNone(client.reset())
