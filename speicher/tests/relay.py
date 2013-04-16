# coding: utf-8
from __future__ import absolute_import, unicode_literals, print_function

from threading import Thread

import pyuv


class Relay(object):
    """Simply echo server."""

    timeout = 10.0

    def __init__(self):
        self._clients = []
        loop = self._loop = pyuv.Loop()
        thread = self._thread = Thread(target=loop.run)
        thread.daemon = True
        self._guard = self._create_guard()
        server = self._server = self._create_acceptor()
        self.host, self.port = server.getsockname()

    def _on_read(self, client, data, error):
        if data is None:
            client.close()
            self._clients.remove(client)
            return
        client.write(data)

    def _on_connection(self, server, error):
        client = pyuv.TCP(server.loop)
        server.accept(client)
        self._clients.append(client)
        client.start_read(self._on_read)

    def _create_acceptor(self):
        server = pyuv.TCP(self._loop)
        server.bind(("0.0.0.0", 0))
        server.listen(self._on_connection)
        return server

    def _on_signal(self, handle):
        self._guard.close()
        self._server.close()

    def _create_guard(self):
        return pyuv.Async(self._loop, self._on_signal)

    def start(self):
        self._thread.start()

    def stop(self):
        self._guard.send()
        self._thread.join(self.timeout)
