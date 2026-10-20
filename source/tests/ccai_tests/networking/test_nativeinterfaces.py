"""
    .. module:: test_nativeinterfaces
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Unit tests for the :mod:`ccai.networking.nativeinterfaces` module.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>

The ``sockaddr``, ``getifaddrs()`` entry and Windows adapter-list tests build their structures in memory, so they run on
every platform. The tests that call ``getifaddrs()`` are skipped on Windows, and the test that calls
``GetAdaptersAddresses()`` runs on Windows only.
"""

import ctypes
import ipaddress
import re
import socket
import struct
import sys
import unittest

from typing import List

from ccai.networking.nativeinterfaces import (
    IFF_BROADCAST,
    IFF_POINTOPOINT,
    IfAddrs,
    IpAdapterAddresses,
    IpAdapterUnicastAddress,
    address_entry,
    interface_addresses,
    ipv4_address_text,
    ipv4_broadcast_from_prefix,
    ipv4_netmask_from_prefix,
    ipv6_address_text,
    ipv6_netmask_from_prefix,
    ipv6_netmask_text,
    list_interfaces,
    parse_adapter_list,
    read_interface_table,
    read_posix_interface_table,
    read_sockaddr,
    read_windows_interface_table,
)


def _sockaddr_in(address: str) -> bytes:
    """
        A ``sockaddr_in`` laid out the Linux and Windows way: a 16-bit family, a port and the address.
    """
    rtnval = struct.pack("=HH", socket.AF_INET, 0) + socket.inet_aton(address) + b"\x00" * 8
    return rtnval


def _bsd_sockaddr_in(address: str) -> bytes:
    """
        A ``sockaddr_in`` laid out the BSD way: a length byte, a family byte, a port and the address.
    """
    rtnval = struct.pack("=BBH", 16, socket.AF_INET, 0) + socket.inet_aton(address) + b"\x00" * 8
    return rtnval


def _sockaddr_in6(address: str, scope_id: int = 0) -> bytes:
    """
        A ``sockaddr_in6`` laid out the Linux and Windows way.
    """
    rtnval = struct.pack("=HHI", socket.AF_INET6, 0, 0) + socket.inet_pton(socket.AF_INET6, address)
    rtnval = rtnval + struct.pack("=I", scope_id)
    return rtnval


def _read(raw: bytes, has_length_byte: bool) -> tuple:
    """
        Reads a ``sockaddr`` from a buffer holding ``raw``.
    """
    buffer = ctypes.create_string_buffer(raw, len(raw))
    rtnval = read_sockaddr(ctypes.addressof(buffer), has_length_byte=has_length_byte)
    return rtnval


def _loopback_entries(table: dict) -> list:
    """
        The ``(interface, netmask)`` of every IPv4 address ``127.0.0.1`` in a table.
    """
    rtnval = []
    for name, families in table.items():
        for details in families.get(socket.AF_INET, []):
            if details["addr"] == "127.0.0.1":
                rtnval.append((name, details["netmask"]))
    return rtnval


class SockaddrTests(unittest.TestCase):
    """
        Verifies ``sockaddr`` values read the same in the BSD and Linux/Windows layouts and format as netifaces did.
    """

    def test_an_ipv4_sockaddr_reads_the_same_in_both_layouts(self) -> None:
        """
            The family and address of a ``sockaddr_in`` read the same from the Linux layout and the BSD layout.
        """
        linux_family, linux_raw = _read(_sockaddr_in("192.168.1.10"), has_length_byte=False)
        bsd_family, bsd_raw = _read(_bsd_sockaddr_in("192.168.1.10"), has_length_byte=True)

        self.assertEqual((linux_family, ipv4_address_text(linux_raw)), (socket.AF_INET, "192.168.1.10"))
        self.assertEqual((bsd_family, ipv4_address_text(bsd_raw)), (socket.AF_INET, "192.168.1.10"))
        return

    def test_a_short_bsd_netmask_is_padded_with_zeros(self) -> None:
        """
            A BSD netmask of length 5 holding ``255`` and no family is ``255.0.0.0``.
        """
        family, raw = _read(bytes([5, 0, 0, 0, 255]), has_length_byte=True)

        self.assertEqual((family, len(raw), ipv4_address_text(raw)), (0, 5, "255.0.0.0"))
        return

    def test_an_ipv6_sockaddr_gives_its_address_and_netmask(self) -> None:
        """
            The address of a ``sockaddr_in6`` with no scope is its plain text, and a netmask is ``<mask>/<prefix>``.
        """
        family, raw = _read(_sockaddr_in6("2001:db8::42"), has_length_byte=False)
        _, mask_raw = _read(_sockaddr_in6("ffff:ffff:ffff:ffff::"), has_length_byte=False)

        self.assertEqual((family, ipv6_address_text(raw)), (socket.AF_INET6, "2001:db8::42"))
        self.assertEqual(ipv6_netmask_text(mask_raw), "ffff:ffff:ffff:ffff::/64")
        return

    def test_a_scoped_ipv6_address_carries_its_zone(self) -> None:
        """
            An IPv6 address with a scope id is written with a zone (``%``), as netifaces wrote it.
        """
        interface_index = socket.if_nameindex()[0][0]
        _, raw = _read(_sockaddr_in6("fe80::1", scope_id=interface_index), has_length_byte=False)

        self.assertTrue(ipv6_address_text(raw).startswith("fe80::1%"))
        return

    def test_no_pointer_is_no_address(self) -> None:
        """
            A null ``sockaddr`` pointer reads as no address.
        """
        self.assertEqual(read_sockaddr(None), (socket.AF_UNSPEC, b""))
        self.assertEqual(read_sockaddr(0), (socket.AF_UNSPEC, b""))
        return

    def test_prefix_lengths_become_netmasks_and_broadcast_addresses(self) -> None:
        """
            Windows gives prefix lengths: they become netmasks and broadcast addresses written as netifaces wrote them.
        """
        self.assertEqual(ipv4_netmask_from_prefix(24), "255.255.255.0")
        self.assertEqual(ipv4_netmask_from_prefix(8), "255.0.0.0")
        self.assertEqual(ipv4_broadcast_from_prefix("192.168.1.10", 24), "192.168.1.255")
        self.assertEqual(ipv6_netmask_from_prefix(64), "ffff:ffff:ffff:ffff::/64")
        self.assertEqual(ipv6_netmask_from_prefix(128), "ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff/128")
        return


class InMemoryStructureTests(unittest.TestCase):
    """
        Verifies ``getifaddrs()`` entries and Windows adapter lists built in memory give the addresses netifaces gave.
    """

    def setUp(self) -> None:
        self.objects: List[object] = []
        return

    def _sockaddr(self, raw: bytes) -> int:
        buffer = ctypes.create_string_buffer(raw, len(raw))
        self.objects.append(buffer)
        rtnval = ctypes.addressof(buffer)
        return rtnval

    def _ifaddrs(self, *, flags: int, addr: bytes, netmask: bytes = b"", other: bytes = b"") -> IfAddrs:
        entry = IfAddrs()
        entry.ifa_name = b"test0"
        entry.ifa_flags = flags
        entry.ifa_addr = self._sockaddr(addr)
        if len(netmask) > 0:
            entry.ifa_netmask = self._sockaddr(netmask)
        if len(other) > 0:
            entry.ifa_broadaddr = self._sockaddr(other)
        self.objects.append(entry)
        return entry

    def _unicast(self, raw: bytes, prefix_length: int) -> IpAdapterUnicastAddress:
        address = IpAdapterUnicastAddress()
        address.Address.lpSockaddr = self._sockaddr(raw)
        address.Address.iSockaddrLength = len(raw)
        address.OnLinkPrefixLength = prefix_length
        self.objects.append(address)
        return address

    def test_a_broadcast_interface_entry_gives_address_netmask_and_broadcast(self) -> None:
        """
            An IPv4 entry on a broadcast interface gives ``addr``, ``netmask`` and ``broadcast``.
        """
        entry = self._ifaddrs(flags=IFF_BROADCAST, addr=_sockaddr_in("192.168.1.10"), netmask=_sockaddr_in("255.255.255.0"),
                              other=_sockaddr_in("192.168.1.255"))

        self.assertEqual(
            address_entry(entry, has_length_byte=False),
            (socket.AF_INET, {"addr": "192.168.1.10", "netmask": "255.255.255.0", "broadcast": "192.168.1.255"}),
        )
        return

    def test_a_point_to_point_or_loopback_entry_gives_a_peer(self) -> None:
        """
            On an interface that is not a broadcast interface the second address is the ``peer``.
        """
        tunnel = self._ifaddrs(flags=IFF_POINTOPOINT, addr=_sockaddr_in("10.8.0.2"), netmask=_sockaddr_in("255.255.255.255"),
                               other=_sockaddr_in("10.8.0.1"))
        loopback = self._ifaddrs(flags=0, addr=_sockaddr_in6("::1"), other=_sockaddr_in6("::1"))

        self.assertEqual(address_entry(tunnel, has_length_byte=False),
                         (socket.AF_INET, {"addr": "10.8.0.2", "netmask": "255.255.255.255", "peer": "10.8.0.1"}))
        self.assertEqual(address_entry(loopback, has_length_byte=False), (socket.AF_INET6, {"addr": "::1", "peer": "::1"}))
        return

    def test_an_empty_second_address_and_other_families_are_left_out(self) -> None:
        """
            An empty second address is left out, and a link-layer entry gives nothing.
        """
        link_local = self._ifaddrs(flags=0, addr=_sockaddr_in6("fe80::5"), other=b"\x00" * 28)
        link_layer = self._ifaddrs(flags=0, addr=struct.pack("=H", 17) + b"\x00" * 18)

        self.assertEqual(address_entry(link_local, has_length_byte=False), (socket.AF_INET6, {"addr": "fe80::5"}))
        self.assertIsNone(address_entry(link_layer, has_length_byte=False))
        return

    def test_an_adapter_list_gives_each_adapter_its_addresses(self) -> None:
        """
            Adapters are named by their GUIDs; IPv4 addresses get the netmask and broadcast address of their prefix length,
            IPv6 addresses the netmask of theirs, and an adapter with no unicast address has an empty table.
        """
        ipv4 = self._unicast(_sockaddr_in("192.168.1.10"), 24)
        ipv6 = self._unicast(_sockaddr_in6("2001:db8::42"), 64)
        ipv4.Next = ctypes.pointer(ipv6)

        first = IpAdapterAddresses()
        first.AdapterName = b"{11111111-2222-3333-4444-555555555555}"
        first.FirstUnicastAddress = ctypes.pointer(ipv4)

        second = IpAdapterAddresses()
        second.AdapterName = b"{66666666-7777-8888-9999-000000000000}"
        first.Next = ctypes.pointer(second)

        table = parse_adapter_list(ctypes.pointer(first))

        self.assertEqual(table, {
            "{11111111-2222-3333-4444-555555555555}": {
                socket.AF_INET: [{"addr": "192.168.1.10", "netmask": "255.255.255.0", "broadcast": "192.168.1.255"}],
                socket.AF_INET6: [{"addr": "2001:db8::42", "netmask": "ffff:ffff:ffff:ffff::/64"}],
            },
            "{66666666-7777-8888-9999-000000000000}": {},
        })
        return


class OperatingSystemTests(unittest.TestCase):
    """
        Verifies the interfaces of the machine running the tests, on Linux, macOS and Windows.
    """

    @unittest.skipIf(sys.platform == "win32", "Windows has no getifaddrs().")
    def test_getifaddrs_lists_the_loopback_interface_and_system_names(self) -> None:
        """
            ``getifaddrs()`` lists one loopback interface holding ``127.0.0.1`` with the netmask ``255.0.0.0``, and every
            interface it lists is one ``if_nameindex()`` knows.
        """
        table = read_posix_interface_table()
        loopback = _loopback_entries(table)
        system_names = set(name for _, name in socket.if_nameindex())

        self.assertEqual(len(loopback), 1)
        self.assertEqual(loopback[0][1], "255.0.0.0")
        self.assertEqual(sorted(set(table) - system_names), [])
        return

    @unittest.skipUnless(sys.platform == "win32", "GetAdaptersAddresses() is a Windows API.")
    def test_getadaptersaddresses_lists_the_loopback_adapter(self) -> None:
        """
            The loopback adapter holds ``127.0.0.1`` with the netmask ``255.0.0.0``, and adapters are named by GUID.
        """
        table = read_windows_interface_table()
        loopback = _loopback_entries(table)
        guid_pattern = re.compile(r"^\{[0-9A-Fa-f-]{36}\}$")
        names_not_guids = [name for name in table if guid_pattern.match(name) is None]

        self.assertEqual(len(loopback), 1)
        self.assertEqual(loopback[0][1], "255.0.0.0")
        self.assertEqual(names_not_guids, [])
        return

    def test_the_loopback_interface_holds_127_0_0_1(self) -> None:
        """
            One interface's IPv4 addresses include ``127.0.0.1``, found through ``interface_addresses``.
        """
        names = list_interfaces()

        loopback_names = []
        for name in names:
            for details in interface_addresses(name).get(socket.AF_INET, []):
                if details["addr"] == "127.0.0.1":
                    loopback_names.append(name)

        self.assertGreater(len(names), 0)
        self.assertEqual(len(loopback_names), 1)
        return

    def test_an_unknown_interface_is_a_value_error(self) -> None:
        """
            An interface that does not exist raises ValueError, as netifaces did.
        """
        with self.assertRaises(ValueError):
            interface_addresses("no-such-interface-0")
        return

    def test_every_address_and_netmask_is_well_formed(self) -> None:
        """
            Every IPv4 value is a dotted quad, and every IPv6 address parses with a ``<mask>/<prefix>`` netmask.
        """
        problems = []
        for name, families in read_interface_table().items():
            for details in families.get(socket.AF_INET, []):
                for key in ("addr", "netmask", "broadcast", "peer"):
                    if key in details:
                        try:
                            ipaddress.IPv4Address(details[key])
                        except ValueError:
                            problems.append((name, key, details[key]))
            for details in families.get(socket.AF_INET6, []):
                try:
                    ipaddress.IPv6Address(details["addr"].split("%")[0])
                except ValueError:
                    problems.append((name, "addr", details["addr"]))
                if "netmask" in details:
                    mask, _, prefix_length = details["netmask"].partition("/")
                    try:
                        ipaddress.IPv6Address(mask)
                        if not 0 <= int(prefix_length) <= 128:
                            problems.append((name, "netmask", details["netmask"]))
                    except ValueError:
                        problems.append((name, "netmask", details["netmask"]))

        self.assertEqual(problems, [])
        return


if __name__ == "__main__":
    unittest.main()
