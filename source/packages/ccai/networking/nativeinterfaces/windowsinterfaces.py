"""
    .. module:: windowsinterfaces
        :platform: Windows
        :synopsis: Reads the network interfaces and their addresses with ``GetAdaptersAddresses()`` from ``iphlpapi.dll``.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2026, Code Craft AI LLC"
__credits__ = []

import ctypes
import os
import socket

from typing import Any, Dict, List

from ccai.networking.nativeinterfaces.ipadapteraddresses import IpAdapterAddresses
from ccai.networking.nativeinterfaces.sockaddrs import (
    ipv4_address_text,
    ipv4_broadcast_from_prefix,
    ipv4_netmask_from_prefix,
    ipv6_address_text,
    ipv6_netmask_from_prefix,
    read_sockaddr,
)

#: ``GetAdaptersAddresses()`` succeeded.
ERROR_SUCCESS = 0

#: The buffer was too small; the size it needs has been written back.
ERROR_BUFFER_OVERFLOW = 111

#: There are no adapters.
ERROR_NO_DATA = 232

#: Leave out the anycast, multicast and DNS server lists, which this package does not read.
GAA_FLAG_SKIP_ANYCAST_MULTICAST_DNS = 0x0002 | 0x0004 | 0x0008

#: The buffer size Microsoft recommends starting with.
ADAPTER_BUFFER_INITIAL_SIZE = 15000

#: How many times to grow the buffer when adapters appear between calls.
ADAPTER_BUFFER_ATTEMPTS = 4

#: The address family that asks for both IPv4 and IPv6 addresses.
AF_UNSPEC_WINDOWS = 0


def query_adapter_buffer() -> Any:
    """
        Calls ``GetAdaptersAddresses()`` and returns the buffer it filled. The caller keeps the buffer alive while it
        reads the adapters in it.

        :returns: The buffer, or None when there are no adapters.

        :raises: OSError when ``GetAdaptersAddresses()`` fails.
    """
    iphlpapi = ctypes.WinDLL("iphlpapi")
    get_adapters_addresses = iphlpapi.GetAdaptersAddresses
    get_adapters_addresses.argtypes = [
        ctypes.c_uint32, ctypes.c_uint32, ctypes.c_void_p, ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint32)
    ]
    get_adapters_addresses.restype = ctypes.c_uint32

    size = ctypes.c_uint32(ADAPTER_BUFFER_INITIAL_SIZE)
    buffer = None
    result = ERROR_BUFFER_OVERFLOW
    for _ in range(ADAPTER_BUFFER_ATTEMPTS):
        buffer = ctypes.create_string_buffer(size.value)
        result = get_adapters_addresses(AF_UNSPEC_WINDOWS, GAA_FLAG_SKIP_ANYCAST_MULTICAST_DNS, None, buffer, ctypes.byref(size))
        if result != ERROR_BUFFER_OVERFLOW:
            break

    if result == ERROR_NO_DATA:
        return None

    if result != ERROR_SUCCESS:
        err_msg_lines = [
            "GetAdaptersAddresses() failed with error {}: {}".format(result, ctypes.FormatError(result)),
            "BUFFER SIZE: {}".format(size.value),
        ]
        err_msg = os.linesep.join(err_msg_lines)
        raise OSError(result, err_msg)

    return buffer


def parse_adapter_list(first_adapter: Any) -> Dict[str, Dict[int, List[Dict[str, str]]]]:
    """
        Reads the adapters of a ``GetAdaptersAddresses()`` result, with their IPv4 and IPv6 unicast addresses, in the
        shape netifaces gave them. Windows gives a prefix length rather than a netmask, so the IPv4 netmask and broadcast
        address are made from it.

        :param first_adapter: A ``POINTER(IpAdapterAddresses)`` to the first adapter.

        :returns: The adapters by ``AdapterName`` (their GUID, the name netifaces used), each with its addresses by
                  family (``socket.AF_INET`` and ``socket.AF_INET6``).
    """
    table: Dict[str, Dict[int, List[Dict[str, str]]]] = {}

    adapter = first_adapter
    while bool(adapter):
        info = adapter.contents
        name = info.AdapterName.decode("utf-8", errors="replace")
        families: Dict[int, List[Dict[str, str]]] = {}

        unicast = info.FirstUnicastAddress
        while bool(unicast):
            address = unicast.contents
            family, raw = read_sockaddr(address.Address.lpSockaddr, length=address.Address.iSockaddrLength,
                                        has_length_byte=False)
            prefix_length = address.OnLinkPrefixLength

            details = None
            if family == socket.AF_INET:
                text = ipv4_address_text(raw)
                details = {
                    "addr": text,
                    "netmask": ipv4_netmask_from_prefix(prefix_length),
                    "broadcast": ipv4_broadcast_from_prefix(text, prefix_length),
                }
            elif family == socket.AF_INET6:
                details = {"addr": ipv6_address_text(raw), "netmask": ipv6_netmask_from_prefix(prefix_length)}

            if details is not None:
                if family not in families:
                    families[family] = []
                families[family].append(details)

            unicast = address.Next

        table[name] = families
        adapter = info.Next

    return table


def read_windows_interface_table() -> Dict[str, Dict[int, List[Dict[str, str]]]]:
    """
        Reads every network adapter and its IPv4 and IPv6 addresses with ``GetAdaptersAddresses()``.

        :returns: The adapters by ``AdapterName``, each with its addresses by family.

        :raises: OSError when ``GetAdaptersAddresses()`` fails.
    """
    buffer = query_adapter_buffer()
    if buffer is None:
        rtnval: Dict[str, Dict[int, List[Dict[str, str]]]] = {}
        return rtnval

    first_adapter = ctypes.cast(buffer, ctypes.POINTER(IpAdapterAddresses))
    rtnval = parse_adapter_list(first_adapter)
    return rtnval
