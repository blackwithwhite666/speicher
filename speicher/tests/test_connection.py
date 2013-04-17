# coding: utf-8
from __future__ import absolute_import, unicode_literals, print_function

from .base import TestCase
from .relay import Relay

from ..connection import Connection, MAX_READ_LENGTH
from ..exceptions import ConnectionError


class ConnectionTest(TestCase):

    def setUp(self):
        relay = self.relay = Relay()
        self.host, self.port = relay.host, relay.port
        self.addCleanup(relay.stop)
        relay.start()

    def create_connection(self, **kwargs):
        options = dict(host=self.host, port=self.port)
        options.update(kwargs)
        c = Connection(**options)
        self.addCleanup(c.disconnect)
        return c

    def test_send_read(self):
        d = dict(test=1)
        c = self.create_connection()
        c.send(d)
        self.assertEqual(d, c.read())

    def test_multiple_connect(self):
        c = self.create_connection()
        c.connect()
        first_sock = c._sock
        self.assertIsNotNone(first_sock)
        c.connect()
        second_sock = c._sock
        self.assertIs(first_sock, second_sock)

    def test_connection_error(self):
        c = self.create_connection(host='127.1.2.3', port=65434)
        with self.assertRaises(ConnectionError):
            c.connect()

    def test_end_of_file(self):
        c = self.create_connection()
        c.connect()
        self.relay.stop()
        c.send(dict(test=1))
        with self.assertRaises(ConnectionError):
            c.read()

    def test_big_packet(self):
        big_fat_string = '00' * MAX_READ_LENGTH
        c = self.create_connection()
        c.send(big_fat_string)
        self.assertEqual(big_fat_string, c.read())
