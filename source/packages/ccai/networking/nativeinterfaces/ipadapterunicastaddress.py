"""
    .. module:: ipadapterunicastaddress
        :platform: Windows
        :synopsis: The Windows ``IP_ADAPTER_UNICAST_ADDRESS_LH`` structure, laid out for ctypes.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2026, Code Craft AI LLC"
__credits__ = []

import ctypes

from ccai.networking.nativeinterfaces.socketaddress import SocketAddress


class IpAdapterUnicastAddress(ctypes.Structure):
    """
        One unicast address of a network adapter (``IP_ADAPTER_UNICAST_ADDRESS_LH``), in the list that
        ``GetAdaptersAddresses()`` hangs off each adapter. ``OnLinkPrefixLength`` is the length of the address's network
        prefix, from which the netmask is made.

        The structure is declared up to ``OnLinkPrefixLength``, the last member this package reads; the structures are
        only ever read through pointers into the buffer Windows fills, so the members after it do not need to be declared.
        ``ULONG`` and ``DWORD`` are 32 bits on Windows, so they are declared as ``c_uint32``.
    """


IpAdapterUnicastAddress._fields_ = [
    ("Length", ctypes.c_uint32),
    ("Flags", ctypes.c_uint32),
    ("Next", ctypes.POINTER(IpAdapterUnicastAddress)),
    ("Address", SocketAddress),
    ("PrefixOrigin", ctypes.c_int),
    ("SuffixOrigin", ctypes.c_int),
    ("DadState", ctypes.c_int),
    ("ValidLifetime", ctypes.c_uint32),
    ("PreferredLifetime", ctypes.c_uint32),
    ("LeaseLifetime", ctypes.c_uint32),
    ("OnLinkPrefixLength", ctypes.c_uint8),
]
