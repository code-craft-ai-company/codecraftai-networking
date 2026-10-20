"""
    .. module:: test_windowsinterfaces
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Testbase tests for reading adapters with ``GetAdaptersAddresses()``.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>

The parsing test builds ``IP_ADAPTER_ADDRESSES`` structures in memory, so it runs on every platform. The table test calls
``GetAdaptersAddresses()`` and runs on Windows only.
"""

import ctypes
import re
import socket
import struct
import sys

from typing import List

from ccai.errors.exceptions import SkipError

from ccai.networking.nativeinterfaces.ipadapteraddresses import IpAdapterAddresses
from ccai.networking.nativeinterfaces.ipadapterunicastaddress import IpAdapterUnicastAddress
from ccai.networking.nativeinterfaces.windowsinterfaces import parse_adapter_list, read_windows_interface_table


class _AdapterMemory:
    """
        Keeps the structures and buffers of an in-memory adapter list alive while a test reads it.
    """

    def __init__(self) -> None:
        self.objects: List[object] = []
        return

    def unicast(self, raw: bytes, prefix_length: int) -> IpAdapterUnicastAddress:
        """
            A unicast address holding the ``sockaddr`` bytes and the prefix length.
        """
        buffer = ctypes.create_string_buffer(raw, len(raw))
        address = IpAdapterUnicastAddress()
        address.Address.lpSockaddr = ctypes.addressof(buffer)
        address.Address.iSockaddrLength = len(raw)
        address.OnLinkPrefixLength = prefix_length
        self.objects.extend([buffer, address])
        return address


def _sockaddr_in(address: str) -> bytes:
    """
        A ``sockaddr_in`` laid out the Windows way.
    """
    rtnval = struct.pack("=HH", socket.AF_INET, 0) + socket.inet_aton(address) + b"\x00" * 8
    return rtnval


def _sockaddr_in6(address: str) -> bytes:
    """
        A ``sockaddr_in6`` laid out the Windows way, with no scope.
    """
    rtnval = struct.pack("=HHI", socket.AF_INET6, 0, 0) + socket.inet_pton(socket.AF_INET6, address) + struct.pack("=I", 0)
    return rtnval


def test_an_adapter_list_gives_each_adapter_its_addresses() -> None:
    """
        Each adapter is named by its ``AdapterName`` (its GUID), its IPv4 address gets the netmask and broadcast address
        of its prefix length, its IPv6 address the netmask of its prefix length, and an adapter with no unicast address
        has an empty table.
    """
    memory = _AdapterMemory()

    ipv4 = memory.unicast(_sockaddr_in("192.168.1.10"), 24)
    ipv6 = memory.unicast(_sockaddr_in6("2001:db8::42"), 64)
    ipv4.Next = ctypes.pointer(ipv6)

    first = IpAdapterAddresses()
    first.AdapterName = b"{11111111-2222-3333-4444-555555555555}"
    first.FirstUnicastAddress = ctypes.pointer(ipv4)

    second = IpAdapterAddresses()
    second.AdapterName = b"{66666666-7777-8888-9999-000000000000}"
    first.Next = ctypes.pointer(second)

    table = parse_adapter_list(ctypes.pointer(first))

    assert table == {
        "{11111111-2222-3333-4444-555555555555}": {
            socket.AF_INET: [{"addr": "192.168.1.10", "netmask": "255.255.255.0", "broadcast": "192.168.1.255"}],
            socket.AF_INET6: [{"addr": "2001:db8::42", "netmask": "ffff:ffff:ffff:ffff::/64"}],
        },
        "{66666666-7777-8888-9999-000000000000}": {},
    }
    return


def test_getadaptersaddresses_lists_the_loopback_adapter() -> None:
    """
        On Windows, ``GetAdaptersAddresses()`` lists the loopback adapter holding ``127.0.0.1`` with the netmask
        ``255.0.0.0``, and adapters are named by their GUIDs.
    """
    if sys.platform != "win32":
        raise SkipError("GetAdaptersAddresses() is a Windows API.")

    table = read_windows_interface_table()

    loopback = []
    for name, families in table.items():
        for details in families.get(socket.AF_INET, []):
            if details["addr"] == "127.0.0.1":
                loopback.append((name, details["netmask"]))

    guid_pattern = re.compile(r"^\{[0-9A-Fa-f-]{36}\}$")
    names_not_guids = [name for name in table if guid_pattern.match(name) is None]

    assert len(loopback) == 1
    assert loopback[0][1] == "255.0.0.0"
    assert names_not_guids == []
    return
