"""
    .. module:: nativeinterfaces
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Lists network interfaces and their IP addresses through the operating system's own API.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>

The interfaces are read with ctypes, from ``getifaddrs()`` in the C library on Linux and macOS and from
``GetAdaptersAddresses()`` in ``iphlpapi.dll`` on Windows, so no compiled extension is needed. The results have the shape
``netifaces`` gave them:

- :func:`list_interfaces` replaces ``netifaces.interfaces()``
- :func:`interface_addresses` replaces ``netifaces.ifaddresses()``: the addresses of an interface keyed by
  ``socket.AF_INET`` and ``socket.AF_INET6`` (the values of ``netifaces.AF_INET`` and ``netifaces.AF_INET6``), each a
  dict with ``addr`` and ``netmask``, plus ``broadcast`` or ``peer`` when the interface has one

On Windows an interface is named by its adapter GUID, as netifaces named it. Link-layer (MAC) addresses and the IPv6
address ``flags`` netifaces read on macOS are not read.

A ``sockaddr`` starts with a 16-bit address family on Linux and Windows. On the BSDs, macOS among them, it starts with a
one-byte length followed by a one-byte family, and a netmask's ``sockaddr`` may be shorter than a full address (the bytes
it leaves out are zero) or carry no family at all. Past that header the layouts agree: an IPv4 ``sockaddr_in`` holds its
address at bytes 4-7, and an IPv6 ``sockaddr_in6`` holds its flow information at bytes 4-7, its address at bytes 8-23 and
its scope id at bytes 24-27.
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2026, Code Craft AI LLC"
__credits__ = []

import ctypes
import ctypes.util
import ipaddress
import os
import socket
import struct
import sys

from typing import Any, Dict, List, Optional, Tuple

#: Whether a ``sockaddr`` starts with a length byte (the BSDs, macOS among them) rather than a 16-bit family.
SOCKADDR_HAS_LENGTH_BYTE = sys.platform == "darwin" or sys.platform.startswith(("freebsd", "openbsd", "netbsd", "dragonfly"))

#: The size of a ``sockaddr_in``.
SOCKADDR_IN_SIZE = 16

#: The size of a ``sockaddr_in6``.
SOCKADDR_IN6_SIZE = 28

#: ``ifa_broadaddr`` holds a broadcast address (the value is the same on Linux and the BSDs).
IFF_BROADCAST = 0x2

#: ``ifa_broadaddr`` holds the far end of a point-to-point link (the value is the same on Linux and the BSDs).
IFF_POINTOPOINT = 0x10

#: ``GetAdaptersAddresses()`` succeeded.
ERROR_SUCCESS = 0

#: The buffer was too small; the size it needs has been written back.
ERROR_BUFFER_OVERFLOW = 111

#: There are no adapters.
ERROR_NO_DATA = 232

#: Leave out the anycast, multicast and DNS server lists, which this module does not read.
GAA_FLAG_SKIP_ANYCAST_MULTICAST_DNS = 0x0002 | 0x0004 | 0x0008

#: The buffer size Microsoft recommends starting with.
ADAPTER_BUFFER_INITIAL_SIZE = 15000

#: How many times to grow the buffer when adapters appear between calls.
ADAPTER_BUFFER_ATTEMPTS = 4

#: The address family that asks ``GetAdaptersAddresses()`` for both IPv4 and IPv6 addresses.
AF_UNSPEC_WINDOWS = 0

#: An interface table: interface name to its addresses by family.
InterfaceTable = Dict[str, Dict[int, List[Dict[str, str]]]]


class IfAddrs(ctypes.Structure):
    """
        One entry of the list ``getifaddrs()`` returns (``struct ifaddrs``). Linux and the BSDs, macOS among them, lay the
        structure out the same way.

        ``ifa_broadaddr`` is a union of the broadcast address and the destination address of a point-to-point link;
        ``ifa_flags`` says which of the two it holds (``IFF_BROADCAST`` or ``IFF_POINTOPOINT``). The addresses are
        pointers to ``struct sockaddr`` and are read with :func:`read_sockaddr`.
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


class SocketAddress(ctypes.Structure):
    """
        The Windows ``SOCKET_ADDRESS``: a pointer to a ``sockaddr`` and its length in bytes. It is a structure of its own,
        rather than two fields of the structures that hold it, because its alignment decides where the fields after it
        start.
    """

    _fields_ = [
        ("lpSockaddr", ctypes.c_void_p),
        ("iSockaddrLength", ctypes.c_int),
    ]


class IpAdapterUnicastAddress(ctypes.Structure):
    """
        One unicast address of a Windows network adapter (``IP_ADAPTER_UNICAST_ADDRESS_LH``), in the list that
        ``GetAdaptersAddresses()`` hangs off each adapter. ``OnLinkPrefixLength`` is the length of the address's network
        prefix, from which the netmask is made.

        The structure is declared up to ``OnLinkPrefixLength``, the last member this module reads; the structures are only
        ever read through pointers into the buffer Windows fills, so the members after it do not need to be declared.
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


class IpAdapterAddresses(ctypes.Structure):
    """
        One Windows network adapter in the list ``GetAdaptersAddresses()`` fills (``IP_ADAPTER_ADDRESSES_LH``).

        ``AdapterName`` is the adapter's GUID, such as ``{4D36E972-E325-11CE-BFC1-08002BE10318}``, which is the name
        netifaces gave Windows interfaces; ``FriendlyName`` is the name Windows shows, such as ``Ethernet``.

        The structure is declared up to ``FriendlyName``, the last member this module reads; the structures are only ever
        read through pointers into the buffer Windows fills, so the members after it do not need to be declared.
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


def list_interfaces() -> List[str]:
    """
        The names of the network interfaces, as ``netifaces.interfaces()`` gave them. On Windows the name of an interface
        is its adapter GUID.

        :returns: The interface names.

        :raises: OSError when the operating system cannot list the interfaces.
    """
    table = read_interface_table()
    names = list(table.keys())
    return names


def interface_addresses(ifname: str) -> Dict[int, List[Dict[str, str]]]:
    """
        The IP addresses of one network interface, as ``netifaces.ifaddresses()`` gave them: a dict from address family
        (``socket.AF_INET``, ``socket.AF_INET6``) to the list of the interface's addresses of that family.

        :param ifname: The interface name.

        :returns: The addresses by family; empty when the interface has no IP address.

        :raises: ValueError when there is no interface with that name, as ``netifaces.ifaddresses()`` raised.
    """
    table = read_interface_table()
    if ifname not in table:
        err_msg_lines = [
            "There is no network interface named '{}'.".format(ifname),
            "INTERFACES: ({})".format(len(table)),
        ]
        for name in table:
            err_msg_lines.append("    {}".format(name))
        err_msg = os.linesep.join(err_msg_lines)
        raise ValueError(err_msg)

    rtnval = table[ifname]
    return rtnval


def read_interface_table() -> InterfaceTable:
    """
        Reads every network interface and its IP addresses: with ``GetAdaptersAddresses()`` on Windows and with
        ``getifaddrs()`` everywhere else.

        :returns: The interfaces, each with its addresses by family (``socket.AF_INET`` and ``socket.AF_INET6``).

        :raises: OSError when the operating system cannot list the interfaces.
    """
    if sys.platform == "win32":
        table = read_windows_interface_table()
    else:
        table = read_posix_interface_table()
    return table


# ----------------------------------------------------------------------------------------------------------------------
# Reading and formatting sockaddr values
# ----------------------------------------------------------------------------------------------------------------------

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
        The text of the address of a ``sockaddr_in6``. An address with a scope, such as a link-local address, is written
        with its zone the way the operating system writes it (``fe80::1%en0``), as netifaces did.

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


# ----------------------------------------------------------------------------------------------------------------------
# Linux and macOS: getifaddrs()
# ----------------------------------------------------------------------------------------------------------------------

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
        and ``broadcast`` or ``peer``.

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


def read_posix_interface_table() -> InterfaceTable:
    """
        Reads every network interface and its IPv4 and IPv6 addresses with ``getifaddrs()``.

        :returns: The interfaces in the order ``getifaddrs()`` lists them, each with its addresses by family. An interface
                  with no IP address has an empty table.

        :raises: OSError when ``getifaddrs()`` fails.
    """
    library = load_c_library()

    head = ctypes.POINTER(IfAddrs)()
    result = library.getifaddrs(ctypes.byref(head))
    if result != 0:
        errno = ctypes.get_errno()
        errmsg = "getifaddrs() failed: {}".format(os.strerror(errno))
        raise OSError(errno, errmsg)

    table: InterfaceTable = {}
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


# ----------------------------------------------------------------------------------------------------------------------
# Windows: GetAdaptersAddresses()
# ----------------------------------------------------------------------------------------------------------------------

def query_adapter_buffer() -> Any:
    """
        Calls ``GetAdaptersAddresses()`` and returns the buffer it filled. The caller keeps the buffer alive while it reads
        the adapters in it.

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


def parse_adapter_list(first_adapter: Any) -> InterfaceTable:
    """
        Reads the adapters of a ``GetAdaptersAddresses()`` result, with their IPv4 and IPv6 unicast addresses, in the shape
        netifaces gave them. Windows gives a prefix length rather than a netmask, so the IPv4 netmask and broadcast address
        are made from it.

        :param first_adapter: A ``POINTER(IpAdapterAddresses)`` to the first adapter.

        :returns: The adapters by ``AdapterName`` (their GUID, the name netifaces used), each with its addresses by family.
    """
    table: InterfaceTable = {}

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


def read_windows_interface_table() -> InterfaceTable:
    """
        Reads every network adapter and its IPv4 and IPv6 addresses with ``GetAdaptersAddresses()``.

        :returns: The adapters by ``AdapterName``, each with its addresses by family.

        :raises: OSError when ``GetAdaptersAddresses()`` fails.
    """
    buffer = query_adapter_buffer()
    if buffer is None:
        rtnval: InterfaceTable = {}
        return rtnval

    first_adapter = ctypes.cast(buffer, ctypes.POINTER(IpAdapterAddresses))
    rtnval = parse_adapter_list(first_adapter)
    return rtnval
