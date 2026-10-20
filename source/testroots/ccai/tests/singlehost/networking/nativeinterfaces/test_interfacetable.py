"""
    .. module:: test_interfacetable
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Testbase tests for listing interfaces and their addresses on the machine running the tests.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

import ipaddress
import socket

from ccai.networking.nativeinterfaces import interface_addresses, list_interfaces, read_interface_table


def test_the_loopback_interface_holds_127_0_0_1() -> None:
    """
        Every platform lists an interface whose IPv4 addresses include ``127.0.0.1``, and ``interface_addresses`` gives
        that interface's addresses by family.
    """
    names = list_interfaces()

    loopback_names = []
    for name in names:
        addresses = interface_addresses(name)
        for details in addresses.get(socket.AF_INET, []):
            if details["addr"] == "127.0.0.1":
                loopback_names.append(name)

    assert len(names) > 0
    assert len(loopback_names) == 1
    return


def test_an_unknown_interface_is_a_value_error() -> None:
    """
        Asking for the addresses of an interface that does not exist raises ValueError, as netifaces did.
    """
    raised = False
    try:
        interface_addresses("no-such-interface-0")
    except ValueError:
        raised = True

    assert raised
    return


def test_every_address_and_netmask_is_well_formed() -> None:
    """
        Every IPv4 address, netmask and broadcast address is a dotted quad, and every IPv6 address parses (once its zone
        is removed) with a netmask written as ``<mask>/<prefix length>``.
    """
    table = read_interface_table()

    problems = []
    for name, families in table.items():
        for details in families.get(socket.AF_INET, []):
            for key in ("addr", "netmask", "broadcast", "peer"):
                if key in details:
                    try:
                        ipaddress.IPv4Address(details[key])
                    except ValueError:
                        problems.append((name, key, details[key]))
        for details in families.get(socket.AF_INET6, []):
            address = details["addr"].split("%")[0]
            try:
                ipaddress.IPv6Address(address)
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

    assert problems == []
    return
