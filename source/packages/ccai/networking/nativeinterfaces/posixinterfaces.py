"""
    .. module:: posixinterfaces
        :platform: Darwin, Linux, Unix
        :synopsis: Reads the network interfaces and their addresses with ``getifaddrs()`` from the C library.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2026, Code Craft AI LLC"
__credits__ = []

import ctypes
import ctypes.util
import os
import socket

from typing import Any, Dict, List, Optional, Tuple

from ccai.networking.nativeinterfaces.ifaddrs import IfAddrs
from ccai.networking.nativeinterfaces.sockaddrs import (
    SOCKADDR_HAS_LENGTH_BYTE,
    ipv4_address_text,
    ipv6_address_text,
    ipv6_netmask_text,
    read_sockaddr,
)

#: ``ifa_broadaddr`` holds a broadcast address (the value is the same on Linux and the BSDs).
IFF_BROADCAST = 0x2

#: ``ifa_broadaddr`` holds the far end of a point-to-point link (the value is the same on Linux and the BSDs).
IFF_POINTOPOINT = 0x10


def load_c_library() -> Any:
    """
        The C library, with ``getifaddrs`` and ``freeifaddrs`` declared.

        :returns: The library.

        :raises: OSError when no C library with ``getifaddrs`` can be found.
    """
    library = ctypes.CDLL(None, use_errno=True)
    if not hasattr(library, "getifaddrs"):
        library_path = ctypes.util.find_library("c")
        if library_path is None:
            errmsg = "The C library could not be found, so the network interfaces cannot be read."
            raise OSError(errmsg)
        library = ctypes.CDLL(library_path, use_errno=True)

    library.getifaddrs.argtypes = [ctypes.POINTER(ctypes.POINTER(IfAddrs))]
    library.getifaddrs.restype = ctypes.c_int
    library.freeifaddrs.argtypes = [ctypes.POINTER(IfAddrs)]
    library.freeifaddrs.restype = None

    return library


def address_entry(entry: IfAddrs, *, has_length_byte: bool = SOCKADDR_HAS_LENGTH_BYTE) -> Optional[Tuple[int, Dict[str, str]]]:
    """
        The IPv4 or IPv6 address of one ``getifaddrs()`` entry, in the shape netifaces gave it: ``addr``, ``netmask``,
        and ``broadcast`` or ``peer``. The IPv6 ``flags`` that netifaces read on macOS with a separate ``ioctl`` are not
        read.

        :param entry: The entry.
        :param has_length_byte: Whether ``sockaddr`` values start with a length byte, as on the BSDs.

        :returns: ``(AF_INET or AF_INET6, the address)``, or None for an entry with no address or another kind of address
                  (such as a link-layer address).
    """
    family, raw = read_sockaddr(entry.ifa_addr, has_length_byte=has_length_byte)

    if family == socket.AF_INET:
        details = {"addr": ipv4_address_text(raw)}
        if entry.ifa_netmask:
            _, mask_raw = read_sockaddr(entry.ifa_netmask, has_length_byte=has_length_byte)
            details["netmask"] = ipv4_address_text(mask_raw)
        if entry.ifa_broadaddr:
            other_family, other_raw = read_sockaddr(entry.ifa_broadaddr, has_length_byte=has_length_byte)
            if other_family == family:
                details[_second_address_key(entry.ifa_flags)] = ipv4_address_text(other_raw)
    elif family == socket.AF_INET6:
        details = {"addr": ipv6_address_text(raw)}
        if entry.ifa_netmask:
            _, mask_raw = read_sockaddr(entry.ifa_netmask, has_length_byte=has_length_byte)
            details["netmask"] = ipv6_netmask_text(mask_raw)
        if entry.ifa_broadaddr:
            other_family, other_raw = read_sockaddr(entry.ifa_broadaddr, has_length_byte=has_length_byte)
            if other_family == family:
                details[_second_address_key(entry.ifa_flags)] = ipv6_address_text(other_raw)
    else:
        return None

    rtnval = (family, details)
    return rtnval


def _second_address_key(flags: int) -> str:
    """
        The key netifaces gave the second address of an entry (``ifa_broadaddr``): ``broadcast`` when the interface is a
        broadcast interface, and ``peer`` otherwise, which covers point-to-point links and loopback. The second address
        is only taken when it is of the entry's own family; an empty one (as on IPv6 link-local entries) is left out.

        :param flags: The entry's ``ifa_flags``.

        :returns: ``broadcast`` or ``peer``.
    """
    if flags & IFF_BROADCAST:
        rtnval = "broadcast"
    else:
        rtnval = "peer"
    return rtnval


def read_posix_interface_table() -> Dict[str, Dict[int, List[Dict[str, str]]]]:
    """
        Reads every network interface and its IPv4 and IPv6 addresses with ``getifaddrs()``.

        :returns: The interfaces in the order ``getifaddrs()`` lists them, each with its addresses by family
                  (``socket.AF_INET`` and ``socket.AF_INET6``). An interface with no IP address has an empty table.

        :raises: OSError when ``getifaddrs()`` fails.
    """
    library = load_c_library()

    head = ctypes.POINTER(IfAddrs)()
    result = library.getifaddrs(ctypes.byref(head))
    if result != 0:
        errno = ctypes.get_errno()
        errmsg = "getifaddrs() failed: {}".format(os.strerror(errno))
        raise OSError(errno, errmsg)

    table: Dict[str, Dict[int, List[Dict[str, str]]]] = {}
    try:
        cursor = head
        while bool(cursor):
            entry = cursor.contents
            name = entry.ifa_name.decode("utf-8", errors="replace")
            if name not in table:
                table[name] = {}

            found = address_entry(entry)
            if found is not None:
                family, details = found
                if family not in table[name]:
                    table[name][family] = []
                table[name][family].append(details)

            cursor = entry.ifa_next
    finally:
        library.freeifaddrs(head)

    return table
