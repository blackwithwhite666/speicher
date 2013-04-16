# coding: utf-8
from __future__ import absolute_import, unicode_literals, print_function

from .base import TestCase
from .relay import Relay

from ..connection import Connection


class ConnectionTest(TestCase):

    def setUp(self):
        relay = Relay()
        self.host, self.port = relay.host, relay.port
        self.addCleanup(relay.stop)
        relay.start()

    def test_send_read(self):
        d = dict(test=1)
        c = Connection(host=self.host, port=self.port)
        c.send(d)
        self.assertEqual(d, c.read())
