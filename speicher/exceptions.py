# coding: utf-8
"""Contains library errors."""
from __future__ import absolute_import, unicode_literals, print_function


class SpeicherError(Exception):
    """Generic library error."""

    def __init__(self, *args, **kwargs):
        for key, value in kwargs.iteritems():
            setattr(self, key, value)
        super(SpeicherError, self).__init__(*args)


class ConnectionError(SpeicherError):
    """Raised on socket error."""


class MalformedReply(SpeicherError):
    """Raised if wrong reply returned by server."""


class ClientError(SpeicherError):
    """Raised on client error (status code 4xx)."""


class ServerError(SpeicherError):
    """Raised on server error (status code 5xx)."""
