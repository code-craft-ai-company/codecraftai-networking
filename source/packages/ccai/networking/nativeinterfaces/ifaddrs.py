"""
    .. module:: ifaddrs
        :platform: Darwin, Linux, Unix
        :synopsis: The ``struct ifaddrs`` that ``getifaddrs()`` returns, laid out for ctypes.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2026, Code Craft AI LLC"
__credits__ = []

import ctypes


class IfAddrs(ctypes.Structure):
    """
        One entry of the list ``getifaddrs()`` returns (``struct ifaddrs``). Linux and the BSDs, macOS among them, lay the
        structure out the same way.

        ``ifa_broadaddr`` is a union of the broadcast address and the destination address of a point-to-point link;
        ``ifa_flags`` says which of the two it holds (``IFF_BROADCAST`` or ``IFF_POINTOPOINT``). The addresses are
        pointers to ``struct sockaddr`` and are read with :func:`ccai.networking.nativeinterfaces.sockaddrs.read_sockaddr`.
    """


IfAddrs._fields_ = [
    ("ifa_next", ctypes.POINTER(IfAddrs)),
    ("ifa_name", ctypes.c_char_p),
    ("ifa_flags", ctypes.c_uint),
    ("ifa_addr", ctypes.c_void_p),
    ("ifa_netmask", ctypes.c_void_p),
    ("ifa_broadaddr", ctypes.c_void_p),
    ("ifa_data", ctypes.c_void_p),
]
