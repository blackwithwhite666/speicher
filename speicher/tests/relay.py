# coding: utf-8
from __future__ import absolute_import, unicode_literals, print_function

import struct
from io import BytesIO
from threading import Thread
from collections import defaultdict

import anyjson
import pyuv

from ..connection import LENGTH_FORMAT


class Relay(object):
    """Relay that process received data (copy by default)."""

    timeout = 10.0

    def __init__(self, callback=None):
        self._clients = []
        self.callback = callback if callback is not None else lambda d: d
        loop = self._loop = pyuv.Loop()
        thread = self._thread = Thread(target=loop.run)
        thread.daemon = True
        self._guard = self._create_guard()
        server = self._server = self._create_acceptor()
        self.host, self.port = server.getsockname()

    def _process(self, client, data):
        chunk = self.callback(data)
        if chunk:
            client.write(chunk)

    def _close(self, client):
        self._clients.remove(client)
        if not client.closed:
            client.close()

    def _on_read(self, client, data, error):
        if data is None:
            self._close(client)
            return
        try:
            self._process(client, data)
        except:
            self._close(client)
            raise

    def _on_connection(self, server, error):
        client = pyuv.TCP(server.loop)
        client.unref()
        server.accept(client)
        self._clients.append(client)
        client.start_read(self._on_read)

    def _create_acceptor(self):
        server = pyuv.TCP(self._loop)
        server.unref()
        server.bind(("127.0.0.1", 0))
        server.listen(self._on_connection)
        return server

    def _on_signal(self, handle):
        for client in self._clients:
            if client.closed:
                continue
            client.close()
        self._guard.close()
        self._server.close()

    def _create_guard(self):
        return pyuv.Async(self._loop, self._on_signal)

    def start(self):
        self._thread.start()

    def stop(self):
        if self._guard.closed:
            return
        self._guard.send()
        self._thread.join(self.timeout)


class Packet(object):

    def __init__(self):
        self.buf = BytesIO()
        self.length = None
        self.received = 0

    def feed(self, chunk):
        if self.length is None:
            self.length = struct.unpack(LENGTH_FORMAT, chunk[:4])[0]
            assert self.length > 0
            chunk = chunk[4:]
        if chunk:
            self.buf.write(chunk)
            self.received += len(chunk)

    @property
    def ready(self):
        return self.length is not None and self.received == self.length

    @property
    def value(self):
        return anyjson.deserialize(self.buf.getvalue())


class FramedRelay(Relay):
    """Relay that properly decode each received packet."""

    def __init__(self, callback=None):
        super(FramedRelay, self).__init__(callback)
        self._packets = defaultdict(Packet)

    def _encode(self, data):
        payload = anyjson.serialize(data)
        return struct.pack(LENGTH_FORMAT, len(payload)) + payload

    def _close(self, client):
        self._packets.pop(client, None)
        super(FramedRelay, self)._close(client)

    def _process(self, client, data):
        packet = self._packets[client]
        packet.feed(data)
        if packet.ready:
            reply = self.callback(packet.value)
            client.write(self._encode(reply))
            self._packets[client] = Packet()
