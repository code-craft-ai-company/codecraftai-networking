"""
    .. module:: test_posixinterfaces
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Testbase tests for reading interfaces with ``getifaddrs()``.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>

The entry tests build ``struct ifaddrs`` entries in memory, so they run on every platform. The table tests call
``getifaddrs()`` and are skipped on Windows, which does not have it.
"""

import ctypes
import socket
import struct
import sys

from typing import List

from ccai.errors.exceptions import SkipError

from ccai.networking.nativeinterfaces.ifaddrs import IfAddrs
from ccai.networking.nativeinterfaces.posixinterfaces import (
    IFF_BROADCAST,
    IFF_POINTOPOINT,
    address_entry,
    read_posix_interface_table,
)


class _EntryMemory:
    """
        Keeps the buffers an in-memory ``ifaddrs`` entry points at alive while a test reads it.
    """

    def __init__(self) -> None:
        self.buffers: List[ctypes.Array] = []
        return

    def sockaddr(self, raw: bytes) -> int:
        """
            Stores the bytes of a ``sockaddr`` and returns their address.
        """
        buffer = ctypes.create_string_buffer(raw, len(raw))
        self.buffers.append(buffer)
        rtnval = ctypes.addressof(buffer)
        return rtnval


def _sockaddr_in(address: str) -> bytes:
    """
        A ``sockaddr_in`` laid out the Linux way.
    """
    rtnval = struct.pack("=HH", socket.AF_INET, 0) + socket.inet_aton(address) + b"\x00" * 8
    return rtnval


def _sockaddr_in6(address: str) -> bytes:
    """
        A ``sockaddr_in6`` laid out the Linux way, with no scope.
    """
    rtnval = struct.pack("=HHI", socket.AF_INET6, 0, 0) + socket.inet_pton(socket.AF_INET6, address) + struct.pack("=I", 0)
    return rtnval


def _entry(memory: _EntryMemory, *, flags: int, addr: bytes, netmask: bytes = b"", other: bytes = b"") -> IfAddrs:
    """
        An ``ifaddrs`` entry pointing at the given ``sockaddr`` bytes; empty bytes leave the pointer null.
    """
    entry = IfAddrs()
    entry.ifa_name = b"test0"
    entry.ifa_flags = flags
    entry.ifa_addr = memory.sockaddr(addr)
    if len(netmask) > 0:
        entry.ifa_netmask = memory.sockaddr(netmask)
    if len(other) > 0:
        entry.ifa_broadaddr = memory.sockaddr(other)
    return entry


def test_a_broadcast_interface_entry_gives_address_netmask_and_broadcast() -> None:
    """
        An IPv4 entry on a broadcast interface gives ``addr``, ``netmask`` and ``broadcast``.
    """
    memory = _EntryMemory()
    entry = _entry(memory, flags=IFF_BROADCAST, addr=_sockaddr_in("192.168.1.10"), netmask=_sockaddr_in("255.255.255.0"),
                   other=_sockaddr_in("192.168.1.255"))

    found = address_entry(entry, has_length_byte=False)
    assert found == (socket.AF_INET, {"addr": "192.168.1.10", "netmask": "255.255.255.0", "broadcast": "192.168.1.255"})
    return


def test_a_point_to_point_or_loopback_entry_gives_a_peer() -> None:
    """
        On an interface that is not a broadcast interface (point-to-point or loopback) the second address is the
        ``peer``, as netifaces gave it.
    """
    memory = _EntryMemory()
    tunnel = _entry(memory, flags=IFF_POINTOPOINT, addr=_sockaddr_in("10.8.0.2"), netmask=_sockaddr_in("255.255.255.255"),
                    other=_sockaddr_in("10.8.0.1"))
    loopback = _entry(memory, flags=0, addr=_sockaddr_in6("::1"), other=_sockaddr_in6("::1"))

    assert address_entry(tunnel, has_length_byte=False) == (
        socket.AF_INET, {"addr": "10.8.0.2", "netmask": "255.255.255.255", "peer": "10.8.0.1"}
    )
    assert address_entry(loopback, has_length_byte=False) == (socket.AF_INET6, {"addr": "::1", "peer": "::1"})
    return


def test_an_empty_second_address_and_other_families_are_left_out() -> None:
    """
        A second address that is empty (no family, as on IPv6 link-local entries) is left out, and an entry whose
        address is neither IPv4 nor IPv6 (a link-layer address) gives nothing.
    """
    memory = _EntryMemory()
    link_local = _entry(memory, flags=0, addr=_sockaddr_in6("fe80::5"), other=b"\x00" * 28)
    link_layer = _entry(memory, flags=0, addr=struct.pack("=H", 17) + b"\x00" * 18)

    assert address_entry(link_local, has_length_byte=False) == (socket.AF_INET6, {"addr": "fe80::5"})
    assert address_entry(link_layer, has_length_byte=False) is None
    return


def test_getifaddrs_lists_the_loopback_interface() -> None:
    """
        ``getifaddrs()`` lists a loopback interface holding ``127.0.0.1`` with the netmask ``255.0.0.0``.
    """
    if sys.platform == "win32":
        raise SkipError("Windows has no getifaddrs().")

    table = read_posix_interface_table()

    loopback = []
    for name, families in table.items():
        for details in families.get(socket.AF_INET, []):
            if details["addr"] == "127.0.0.1":
                loopback.append((name, details["netmask"]))

    assert len(loopback) == 1
    assert loopback[0][1] == "255.0.0.0"
    return


def test_getifaddrs_names_are_the_system_interface_names() -> None:
    """
        Every interface ``getifaddrs()`` lists is an interface ``if_nameindex()`` knows.
    """
    if sys.platform == "win32":
        raise SkipError("Windows has no getifaddrs().")

    table = read_posix_interface_table()
    system_names = set(name for _, name in socket.if_nameindex())

    unknown = sorted(set(table) - system_names)
    assert len(table) > 0
    assert unknown == []
    return
