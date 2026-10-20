"""
    .. module:: ipadapteraddresses
        :platform: Windows
        :synopsis: The Windows ``IP_ADAPTER_ADDRESSES_LH`` structure, laid out for ctypes.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2026, Code Craft AI LLC"
__credits__ = []

import ctypes

from ccai.networking.nativeinterfaces.ipadapterunicastaddress import IpAdapterUnicastAddress


class IpAdapterAddresses(ctypes.Structure):
    """
        One network adapter in the list ``GetAdaptersAddresses()`` fills (``IP_ADAPTER_ADDRESSES_LH``).

        ``AdapterName`` is the adapter's GUID, such as ``{4D36E972-E325-11CE-BFC1-08002BE10318}``, which is the name
        netifaces gave Windows interfaces; ``FriendlyName`` is the name Windows shows, such as ``Ethernet``.

        The structure is declared up to ``FriendlyName``, the last member this package reads; the structures are only
        ever read through pointers into the buffer Windows fills, so the members after it do not need to be declared.
    """


IpAdapterAddresses._fields_ = [
    ("Length", ctypes.c_uint32),
    ("IfIndex", ctypes.c_uint32),
    ("Next", ctypes.POINTER(IpAdapterAddresses)),
    ("AdapterName", ctypes.c_char_p),
    ("FirstUnicastAddress", ctypes.POINTER(IpAdapterUnicastAddress)),
    ("FirstAnycastAddress", ctypes.c_void_p),
    ("FirstMulticastAddress", ctypes.c_void_p),
    ("FirstDnsServerAddress", ctypes.c_void_p),
    ("DnsSuffix", ctypes.c_wchar_p),
    ("Description", ctypes.c_wchar_p),
    ("FriendlyName", ctypes.c_wchar_p),
]
