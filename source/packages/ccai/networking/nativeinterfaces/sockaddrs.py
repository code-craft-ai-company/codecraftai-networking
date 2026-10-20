"""
    .. module:: sockaddrs
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Reads ``struct sockaddr`` values from memory and formats the addresses and netmasks they hold.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>

A ``sockaddr`` starts with a 16-bit address family on Linux and Windows. On the BSDs, macOS among them, it starts with
a one-byte length followed by a one-byte family, and a netmask's ``sockaddr`` may be shorter than a full address (the
bytes it leaves out are zero) or carry no family at all. Past that header the layouts agree: an IPv4 ``sockaddr_in``
holds its address at bytes 4-7, and an IPv6 ``sockaddr_in6`` holds its flow information at bytes 4-7, its address at
bytes 8-23 and its scope id at bytes 24-27.
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2026, Code Craft AI LLC"
__credits__ = []

import ctypes
import ipaddress
import socket
import struct
import sys

from typing import Optional, Tuple

#: Whether a ``sockaddr`` starts with a length byte (the BSDs, macOS among them) rather than a 16-bit family.
SOCKADDR_HAS_LENGTH_BYTE = sys.platform == "darwin" or sys.platform.startswith(("freebsd", "openbsd", "netbsd", "dragonfly"))

#: The size of a ``sockaddr_in``.
SOCKADDR_IN_SIZE = 16

#: The size of a ``sockaddr_in6``.
SOCKADDR_IN6_SIZE = 28


def read_sockaddr(pointer: Optional[int], *, length: Optional[int] = None,
                  has_length_byte: bool = SOCKADDR_HAS_LENGTH_BYTE) -> Tuple[int, bytes]:
    """
        Reads a ``struct sockaddr`` from memory.

        :param pointer: The address of the ``sockaddr``; None or 0 for no address.
        :param length: The size of the ``sockaddr`` when the caller knows it (Windows gives it); None reads the length
                       byte on the BSDs and the size of the family's ``sockaddr`` elsewhere.
        :param has_length_byte: Whether the ``sockaddr`` starts with a length byte, as on the BSDs.

        :returns: ``(address family, the bytes of the sockaddr)``; ``(AF_UNSPEC, b"")`` for no address.
    """
    if pointer is None or pointer == 0:
        rtnval = (socket.AF_UNSPEC, b"")
        return rtnval

    if has_length_byte:
        size = ctypes.c_uint8.from_address(pointer).value
        family = ctypes.c_uint8.from_address(pointer + 1).value
    else:
        family = ctypes.c_uint16.from_address(pointer).value
        if family == socket.AF_INET:
            size = SOCKADDR_IN_SIZE
        elif family == socket.AF_INET6:
            size = SOCKADDR_IN6_SIZE
        else:
            size = 2

    if length is not None:
        size = length

    raw = b""
    if size > 0:
        raw = ctypes.string_at(pointer, size)

    rtnval = (family, raw)
    return rtnval


def _padded(raw: bytes, size: int) -> bytes:
    """
        Pads the bytes of a ``sockaddr`` with zeros to a size, since a BSD netmask may leave its trailing zero bytes out.

        :param raw: The bytes.
        :param size: The size to pad to.

        :returns: The padded bytes.
    """
    padded = raw
    if len(padded) < size:
        padded = padded + b"\x00" * (size - len(padded))
    return padded


def ipv4_address_text(raw: bytes) -> str:
    """
        The dotted-quad address of a ``sockaddr_in``.

        :param raw: The bytes of the ``sockaddr_in``.

        :returns: The address, such as ``192.168.1.10``.
    """
    padded = _padded(raw, 8)
    packed = padded[4:8]
    rtnval = socket.inet_ntoa(packed)
    return rtnval


def ipv6_address_text(raw: bytes) -> str:
    """
        The text of the address of a ``sockaddr_in6``. An address with a scope, such as a link-local address, is
        written with its zone the way the operating system writes it (``fe80::1%en0``), as netifaces did.

        :param raw: The bytes of the ``sockaddr_in6``.

        :returns: The address.
    """
    padded = _padded(raw, SOCKADDR_IN6_SIZE)
    flowinfo = struct.unpack("!I", padded[4:8])[0]
    packed = padded[8:24]
    scope_id = struct.unpack("=I", padded[24:28])[0]

    text = socket.inet_ntop(socket.AF_INET6, packed)
    if scope_id != 0:
        try:
            host, _ = socket.getnameinfo((text, 0, flowinfo, scope_id), socket.NI_NUMERICHOST | socket.NI_NUMERICSERV)
            text = host
        except OSError:
            # The scope id names no interface the resolver knows; write the zone as its number.
            text = "{}%{}".format(text, scope_id)

    rtnval = text
    return rtnval


def ipv6_netmask_text(raw: bytes) -> str:
    """
        The netmask held in a ``sockaddr_in6``, written the way netifaces wrote it: the mask, a slash and the prefix
        length (``ffff:ffff:ffff:ffff::/64``).

        :param raw: The bytes of the ``sockaddr_in6``.

        :returns: The netmask.
    """
    padded = _padded(raw, 24)
    packed = padded[8:24]
    prefix_length = 0
    for byte in packed:
        prefix_length += bin(byte).count("1")

    mask = socket.inet_ntop(socket.AF_INET6, packed)
    rtnval = "{}/{}".format(mask, prefix_length)
    return rtnval


def ipv4_netmask_from_prefix(prefix_length: int) -> str:
    """
        The dotted-quad netmask of a prefix length.

        :param prefix_length: The prefix length, 0 to 32.

        :returns: The netmask, such as ``255.255.255.0`` for 24.
    """
    network = ipaddress.IPv4Network("0.0.0.0/{}".format(prefix_length))
    rtnval = str(network.netmask)
    return rtnval


def ipv4_broadcast_from_prefix(address: str, prefix_length: int) -> str:
    """
        The broadcast address of the network an IPv4 address is on.

        :param address: The address.
        :param prefix_length: The length of the network prefix.

        :returns: The broadcast address, such as ``192.168.1.255`` for ``192.168.1.10`` with a prefix of 24.
    """
    interface = ipaddress.IPv4Interface("{}/{}".format(address, prefix_length))
    rtnval = str(interface.network.broadcast_address)
    return rtnval


def ipv6_netmask_from_prefix(prefix_length: int) -> str:
    """
        The IPv6 netmask of a prefix length, written the way netifaces wrote it (``ffff:ffff:ffff:ffff::/64``).

        :param prefix_length: The prefix length, 0 to 128.

        :returns: The netmask.
    """
    network = ipaddress.IPv6Network("::/{}".format(prefix_length))
    rtnval = "{}/{}".format(network.netmask, prefix_length)
    return rtnval
