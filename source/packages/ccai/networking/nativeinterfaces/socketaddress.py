"""
    .. module:: socketaddress
        :platform: Windows
        :synopsis: The Windows ``SOCKET_ADDRESS`` structure, laid out for ctypes.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2026, Code Craft AI LLC"
__credits__ = []

import ctypes


class SocketAddress(ctypes.Structure):
    """
        ``SOCKET_ADDRESS``: a pointer to a ``sockaddr`` and its length in bytes. It is a structure of its own, rather
        than two fields of the structures that hold it, because its alignment decides where the fields after it start.
    """

    _fields_ = [
        ("lpSockaddr", ctypes.c_void_p),
        ("iSockaddrLength", ctypes.c_int),
    ]
