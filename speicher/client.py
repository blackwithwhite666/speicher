# coding: utf-8
"""Client implementation."""
from __future__ import absolute_import, unicode_literals, print_function

from six import binary_type, text_type

from .connection import Connection
from .exceptions import MalformedReply, ClientError, ServerError

#: No errors happened.
CODE_OK = 200

#: Key not found.
CODE_NOT_FOUND = 404


class Speicher(object):
    """Client to storage service.

    For example::

       >>> import speicher
       >>> c = speicher.Speicher(host='localhost', port=14567)
       >>> c.set('foo', 'bar')
       True
       >>> c.get('foo')
       'bar'
       >>> c.delete('foo')
       True
       >>> c.reset()
       >>> c.delete('foo')
       False
       >>> c.get('foo')
       None
       >>> c.close()

    """

    def __init__(self, host=None, port=None, timeout=None):
        self._conn = Connection(host, port, timeout)

    def _prepare_key(self, key):
        """Prepare given key."""
        if isinstance(key, text_type):
            key = key.encode('utf-8')
        if not key:
            raise ValueError('Key should not be empty.')
        if not isinstance(key, binary_type):
            raise TypeError('Key {0!r} is not string.'.format(key))
        return key

    def _execute(self, command, **kwargs):
        """Send command to server and return reply."""
        self._conn.send(dict(command=command, **kwargs))
        reply = self._conn.read()
        if not isinstance(reply, dict):
            raise MalformedReply('Reply is not dictionary.')
        if 'status_code' not in reply:
            raise MalformedReply('Key "status_code" not exists in reply.')
        status_code = reply['status_code']
        if 400 <= status_code <= 499:
            raise ClientError(
                "Client Error {0}".format(status_code), status_code=status_code)
        elif 500 <= status_code <= 599:
            raise ServerError(
                "Server Error {0}".format(status_code), status_code=status_code)
        elif status_code != CODE_OK:
            raise MalformedReply(
                'Unsupported status code {0}.'.format(status_code))
        return reply

    def set(self, key, value):
        """Store given value at server with given key. Return nothing.
        If value is ``None`` key will be deleted.

        """
        if value is None:
            self.delete(key)
        else:
            key = self._prepare_key(key)
            self._execute(b'SET', key=key, value=value)

    def get(self, key):
        """Get value from server, return ``None`` if no value found."""
        key = self._prepare_key(key)
        try:
            reply = self._execute(b'GET', key=key)
        except ClientError as exc:
            if exc.status_code == CODE_NOT_FOUND:
                # return ``None`` on not found error.
                return None
            raise  # pragma: nocover
        else:
            try:
                return reply['value']
            except KeyError:
                raise MalformedReply('Key "value" not exists in reply.')

    def delete(self, key):
        """Delete value from server, return ``True`` if value deleted,
        otherwise return ``False``.

        """
        key = self._prepare_key(key)
        try:
            self._execute(b'DEL', key=key)
        except ClientError as exc:
            if exc.status_code == CODE_NOT_FOUND:
                # return ``None`` on not found error.
                return False
            raise  # pragma: nocover
        else:
            return True

    def reset(self):
        """Delete all values from server, return ``True`` if no error happened,
        otherwise return ``False``.

        """
        self._execute(b'RST')

    def close(self):
        """Close connection to server if it exists."""
        self._conn.disconnect()

    def __del__(self):
        self.close()
