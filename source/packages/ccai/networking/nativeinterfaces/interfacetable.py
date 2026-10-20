"""
    .. module:: interfacetable
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Lists the network interfaces and their IP addresses through the operating system's own API.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2026, Code Craft AI LLC"
__credits__ = []

import os
import sys

from typing import Dict, List

from ccai.networking.nativeinterfaces.posixinterfaces import read_posix_interface_table
from ccai.networking.nativeinterfaces.windowsinterfaces import read_windows_interface_table


def read_interface_table() -> Dict[str, Dict[int, List[Dict[str, str]]]]:
    """
        Reads every network interface and its IP addresses: with ``GetAdaptersAddresses()`` on Windows and with
        ``getifaddrs()`` everywhere else.

        :returns: The interfaces, each with its addresses by family (``socket.AF_INET`` and ``socket.AF_INET6``). Each
                  address is a dict with ``addr`` and ``netmask``, and for IPv4 ``broadcast`` or ``peer`` when there is
                  one, as netifaces gave them.

        :raises: OSError when the operating system cannot list the interfaces.
    """
    if sys.platform == "win32":
        table = read_windows_interface_table()
    else:
        table = read_posix_interface_table()
    return table


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
