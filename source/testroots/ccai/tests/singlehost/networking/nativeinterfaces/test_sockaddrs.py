"""
    .. module:: test_sockaddrs
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Testbase tests for reading ``sockaddr`` values from memory and formatting their addresses.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

import ctypes
import socket
import struct

from ccai.networking.nativeinterfaces.sockaddrs import (
    ipv4_address_text,
    ipv4_broadcast_from_prefix,
    ipv4_netmask_from_prefix,
    ipv6_address_text,
    ipv6_netmask_from_prefix,
    ipv6_netmask_text,
    read_sockaddr,
)


def _linux_sockaddr_in(address: str) -> bytes:
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


def _linux_sockaddr_in6(address: str, scope_id: int = 0) -> bytes:
    """
        A ``sockaddr_in6`` laid out the Linux and Windows way.
    """
    rtnval = struct.pack("=HH", socket.AF_INET6, 0) + struct.pack("!I", 0) + socket.inet_pton(socket.AF_INET6, address)
    rtnval = rtnval + struct.pack("=I", scope_id)
    return rtnval


def _read(raw: bytes, has_length_byte: bool) -> tuple:
    """
        Reads a ``sockaddr`` from a buffer holding ``raw``.
    """
    buffer = ctypes.create_string_buffer(raw, len(raw))
    rtnval = read_sockaddr(ctypes.addressof(buffer), has_length_byte=has_length_byte)
    return rtnval


def test_an_ipv4_sockaddr_reads_the_same_in_both_layouts() -> None:
    """
        The family and address of a ``sockaddr_in`` read the same from the Linux layout (a 16-bit family) and the BSD
        layout (a length byte and a family byte).
    """
    linux_family, linux_raw = _read(_linux_sockaddr_in("192.168.1.10"), has_length_byte=False)
    bsd_family, bsd_raw = _read(_bsd_sockaddr_in("192.168.1.10"), has_length_byte=True)

    assert (linux_family, ipv4_address_text(linux_raw)) == (socket.AF_INET, "192.168.1.10")
    assert (bsd_family, ipv4_address_text(bsd_raw)) == (socket.AF_INET, "192.168.1.10")
    return


def test_a_short_bsd_netmask_is_padded_with_zeros() -> None:
    """
        A BSD netmask ``sockaddr`` may be shorter than a full address and carry no family; the bytes it leaves out are
        zero, so a length of 5 holding ``255`` is ``255.0.0.0``.
    """
    family, raw = _read(bytes([5, 0, 0, 0, 255]), has_length_byte=True)

    assert (family, len(raw), ipv4_address_text(raw)) == (0, 5, "255.0.0.0")
    return


def test_an_ipv6_sockaddr_gives_its_address_and_netmask() -> None:
    """
        The address of a ``sockaddr_in6`` with no scope is its plain text, and a netmask ``sockaddr_in6`` is written as
        the mask, a slash and the prefix length.
    """
    family, raw = _read(_linux_sockaddr_in6("2001:db8::42"), has_length_byte=False)
    _, mask_raw = _read(_linux_sockaddr_in6("ffff:ffff:ffff:ffff::"), has_length_byte=False)

    assert (family, ipv6_address_text(raw)) == (socket.AF_INET6, "2001:db8::42")
    assert ipv6_netmask_text(mask_raw) == "ffff:ffff:ffff:ffff::/64"
    return


def test_a_scoped_ipv6_address_carries_its_zone() -> None:
    """
        An IPv6 address with a scope id is written with a zone (``%``), as netifaces wrote it.
    """
    loopback_index = socket.if_nameindex()[0][0]
    _, raw = _read(_linux_sockaddr_in6("fe80::1", scope_id=loopback_index), has_length_byte=False)

    text = ipv6_address_text(raw)
    assert text.startswith("fe80::1%")
    return


def test_no_pointer_is_no_address() -> None:
    """
        A null ``sockaddr`` pointer reads as no address.
    """
    assert read_sockaddr(None) == (socket.AF_UNSPEC, b"")
    assert read_sockaddr(0) == (socket.AF_UNSPEC, b"")
    return


def test_prefix_lengths_become_netmasks_and_broadcast_addresses() -> None:
    """
        Windows gives prefix lengths: 24 is ``255.255.255.0`` with the broadcast address ``.255``, and an IPv6 prefix of
        64 or 128 is written the way netifaces wrote IPv6 netmasks.
    """
    assert ipv4_netmask_from_prefix(24) == "255.255.255.0"
    assert ipv4_netmask_from_prefix(8) == "255.0.0.0"
    assert ipv4_broadcast_from_prefix("192.168.1.10", 24) == "192.168.1.255"
    assert ipv6_netmask_from_prefix(64) == "ffff:ffff:ffff:ffff::/64"
    assert ipv6_netmask_from_prefix(128) == "ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff/128"
    return
