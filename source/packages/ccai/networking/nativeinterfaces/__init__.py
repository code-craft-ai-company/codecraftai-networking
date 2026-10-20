"""
    .. module:: nativeinterfaces
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Package that lists network interfaces and their IP addresses through the operating system's own API.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>

The interfaces are read with ctypes, from ``getifaddrs()`` in the C library on Linux and macOS and from
``GetAdaptersAddresses()`` in ``iphlpapi.dll`` on Windows, so no compiled extension is needed. The results have the
shape ``netifaces`` gave them:

- :func:`list_interfaces` replaces ``netifaces.interfaces()``
- :func:`interface_addresses` replaces ``netifaces.ifaddresses()``, keyed by ``socket.AF_INET`` and ``socket.AF_INET6``
  (the values of ``netifaces.AF_INET`` and ``netifaces.AF_INET6``)

Link-layer (MAC) addresses are not read.
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2026, Code Craft AI LLC"
__credits__ = []

from ccai.networking.nativeinterfaces.interfacetable import (
    interface_addresses,
    list_interfaces,
    read_interface_table,
)

__all__ = [
    "interface_addresses",
    "list_interfaces",
    "read_interface_table",
]
