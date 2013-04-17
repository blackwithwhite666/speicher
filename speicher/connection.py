# coding: utf-8
"""Connection implementation."""
from __future__ import absolute_import, unicode_literals, print_function

import struct
import socket
from io import BytesIO

import anyjson

from .exceptions import ConnectionError

#: Format to encode message length.
LENGTH_FORMAT = b'!i'

#: How many bytes should we receive from socket?
MAX_READ_LENGTH = 1000000


class Connection(object):
    """Represent connection to storage. Work with plain TCP connection."""

    length_size = struct.calcsize(LENGTH_FORMAT)
    length_struct = struct.Struct(LENGTH_FORMAT)

    def __init__(self, host=None, port=None, timeout=None):
        self._sock = None
        self.host = host or b'localhost'
        self.port = port or 14567
        self.timeout = timeout or 10.0

    @staticmethod
    def _decode_packet(msg):
        """Decode given message from JSON."""
        return anyjson.deserialize(msg)

    @staticmethod
    def _encode_packet(data):
        """Encode given data to JSON."""
        return anyjson.serialize(data)

    def _create_connection(self):
        """Create a TCP socket connection."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(self.timeout)
        sock.connect((self.host, self.port))
        return sock

    def connect(self):
        """Connects to the server if not already connected."""
        if self._sock is not None:
            return
        try:
            sock = self._create_connection()
        except IOError as exc:
            msg = b"Error connecting {0}:{1}. {2}.".format(
                self.host, self.port, exc.args)
            raise ConnectionError(msg)
        else:
            self._sock = sock

    def disconnect(self):
        """Disconnects from the server and close socket."""
        if self._sock is None:
            return
        try:
            self._sock.close()
        except IOError:  # pragma: nocover
            pass
        finally:
            self._sock = None

    def __del__(self):
        """Close socket in GC."""
        self.disconnect()

    def _create_packet(self, data):
        """Convert data to packet. Simply prepend packet length with right
        format.

        """
        payload = self._encode_packet(data)
        return self.length_struct.pack(len(payload)) + payload

    def send(self, data):
        """Send given data to the server."""
        if self._sock is None:
            self.connect()
        try:
            # send packed message to server
            self._sock.sendall(self._create_packet(data))
        except IOError as exc:
            self.disconnect()
            raise ConnectionError(
                b"Error happened while writing to socket. {0}."
                .format(exc.args))
        except Exception:  # pragma: nocover
            self.disconnect()
            raise

    def _recv_msg(self, length):
        msg = self._sock.recv(length)
        if len(msg) == 0:
            raise ConnectionError(
                b"Error reading from socket: end-of-file.")
        return msg

    def _read_length(self):
        """Read length from socket."""
        buf = self._recv_msg(self.length_size)
        try:
            length = self.length_struct.unpack(buf)[0]
        except struct.error:
            raise ConnectionError(b"Packet length can't be read.")
        if length <= 0:
            raise ConnectionError(b"Packet length should be positive integer.")
        return length

    def _read_payload(self, bytes_left):
        """Read payload from socket."""
        # create buffer to read into
        buf = BytesIO()
        try:
            # read from socket by small chunk
            while bytes_left > 0:
                read_len = min(bytes_left, MAX_READ_LENGTH)
                chunk = self._recv_msg(read_len)
                buf.write(chunk)
                bytes_left -= len(chunk)
            return buf.getvalue()
        finally:
            buf.close()

    def read(self):
        """Read the response from a previously sent command."""
        assert self._sock is not None
        try:
            length = self._read_length()
            payload = self._read_payload(length)
            data = self._decode_packet(payload)
        except (IOError, socket.timeout) as exc:
            self.disconnect()
            raise ConnectionError(
                b"Error while reading from socket: {0}"
                .format(exc.args))
        except Exception:  # pragma: nocover
            self.disconnect()
            raise
        else:
            return data
