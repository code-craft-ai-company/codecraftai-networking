"""
    .. module:: resolution
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Contains helper functions for resolving ip addresses.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []

from typing import Any, List, Optional

import socket as _socket
import netifaces
import os

ARPING_RANGE_CMD = """/bin/bash -c 'for i in {1..254} ;do ping %s.$i -w 5 -c 1 > /dev/null 2>&1 & echo "%s.$i" & done; wait < <(jobs -p); echo Done' """

from automojo.networking.constants import REGEX_IPV4_COMPONENTS, REGEX_IPV6_COMPONENTS

# ---------------------------------------------------------------------------
# Cross-repository type imports.
#
# ``SemanticError`` (automojo-errors), ``Aspects`` (automojo-interfaces),
# ``AddressPlane`` and ``IVPNClient`` (automojo-interfaces) are core
# dependencies. They are imported hard so a missing or mis-pathed core
# dependency fails loudly at import time. A previous ImportError fallback
# defined a SEPARATE ``SemanticError`` class, so callers' ``except`` /
# ``isinstance`` against the canonical type silently missed it.
# ---------------------------------------------------------------------------

from automojo.errors.exceptions import SemanticError
from automojo.aspects.aspects import Aspects
from automojo.interfaces.addressplane import AddressPlane
from automojo.interfaces.ivpnclient import IVPNClient


_OVERLAY_DNS_RESOLVER: Optional[Any] = None


def register_overlay_dns_resolver(*, resolver: Optional[Any]) -> None:
    """
        Register the overlay DNS resolver instance used by
        :func:`resolve_in_plane` when ``plane == AddressPlane.OVERLAY``
        and the injected ``vpn_client`` lookup misses.

        Passing ``None`` clears the registration (useful for test
        teardown).

        :param resolver: An object exposing ``resolve(*, name, aspects)
            -> Optional[str]``, or ``None`` to clear.

        :returns: ``None``.
    """
    global _OVERLAY_DNS_RESOLVER
    _OVERLAY_DNS_RESOLVER = resolver
    return


def get_overlay_dns_resolver() -> Optional[Any]:
    """
        Return the currently-registered overlay DNS resolver, or
        ``None`` when none has been registered.

        :returns: The registered resolver, or ``None``.
    """
    rtnval = _OVERLAY_DNS_RESOLVER
    return rtnval


def _resolve_public(*, name: str, aspects: Aspects) -> Optional[str]:
    """
        Resolve ``name`` on the public plane via the OS public DNS
        resolver. Wraps :func:`socket.gethostbyname` and honours
        ``aspects.connection_timeout`` via :func:`socket.setdefaulttimeout`
        for the duration of the call.

        :param name: Host name to resolve.
        :param aspects: Behaviour controls.

        :returns: Address string, or ``None`` when resolution fails.
    """
    rtnval: Optional[str] = None
    prev_timeout = _socket.getdefaulttimeout()
    try:
        _socket.setdefaulttimeout(aspects.connection_timeout)
        try:
            candidate = _socket.gethostbyname(name)
            rtnval = candidate
        except _socket.gaierror:
            rtnval = None
        except _socket.timeout:
            rtnval = None
        except OSError:
            rtnval = None
    finally:
        _socket.setdefaulttimeout(prev_timeout)
    return rtnval


def _resolve_private(*, name: str, aspects: Aspects) -> Optional[str]:
    """
        Resolve ``name`` on the private plane. The current networking
        package has no distinct private-DNS resolver, so the private
        path delegates to the same OS resolver as the public path but
        is kept as a separate function so callers and overlay/private
        paths remain trivially differentiable in tests and traces.

        :param name: Host name to resolve.
        :param aspects: Behaviour controls.

        :returns: Address string, or ``None`` when resolution fails.
    """
    rtnval = _resolve_public(name=name, aspects=aspects)
    return rtnval


def _resolve_overlay(
    *,
    name: str,
    aspects: Aspects,
    vpn_client: Optional[IVPNClient],
) -> Optional[str]:
    """
        Resolve ``name`` on the overlay plane.

        Consults the injected ``vpn_client.peer_addresses()`` map
        first; on a miss, falls through to the module-registered
        overlay DNS resolver (if any). Never falls back to the public
        or private resolvers.

        :param name: Host name to resolve.
        :param aspects: Behaviour controls.
        :param vpn_client: Optional overlay client to consult first.

        :returns: Address string, or ``None`` when no overlay resolver
            answers.
    """
    rtnval: Optional[str] = None

    if vpn_client is not None:
        peers = vpn_client.peer_addresses()
        if name in peers:
            rtnval = peers[name]

    if rtnval is None:
        resolver = _OVERLAY_DNS_RESOLVER
        if resolver is not None:
            candidate = resolver.resolve(name=name, aspects=aspects)
            rtnval = candidate

    return rtnval


def resolve_in_plane(
    *,
    name: str,
    plane: AddressPlane,
    aspects: Aspects,
    vpn_client: Optional[IVPNClient] = None,
) -> Optional[str]:
    """
        Resolve ``name`` to an address on the requested
        :class:`AddressPlane`.

        Dispatch is sealed: ``PUBLIC`` and ``PRIVATE`` consult the
        respective OS resolvers; ``OVERLAY`` consults the injected
        ``vpn_client`` first and then the module-registered overlay DNS
        resolver. ``OVERLAY`` MUST NOT fall back to ``PUBLIC`` or
        ``PRIVATE``: the caller declares the plane, the framework does
        not classify addresses by network range.

        :param name: Host name (short or FQDN) to resolve.
        :param plane: Which plane to consult.
        :param aspects: Behaviour controls (timeout, retries, logging).
        :param vpn_client: Optional overlay client consulted first when
            ``plane == AddressPlane.OVERLAY``.

        :returns: Address string, or ``None`` when no resolver answers.
        :raises: :class:`SemanticError` when ``name`` is empty or
            ``plane`` is an unknown :class:`AddressPlane` member.
    """
    if len(name) == 0:
        err_msg_lines = ["resolve_in_plane requires a non-empty 'name'."]
        err_msg = os.linesep.join(err_msg_lines)
        raise SemanticError(err_msg)

    rtnval: Optional[str] = None

    if plane == AddressPlane.PUBLIC:
        rtnval = _resolve_public(name=name, aspects=aspects)
    elif plane == AddressPlane.PRIVATE:
        rtnval = _resolve_private(name=name, aspects=aspects)
    elif plane == AddressPlane.OVERLAY:
        rtnval = _resolve_overlay(name=name, aspects=aspects, vpn_client=vpn_client)
    else:
        err_msg_lines = [
            "resolve_in_plane has no branch for the supplied AddressPlane member.",
            f"    plane: {plane!r}",
        ]
        err_msg = os.linesep.join(err_msg_lines)
        raise SemanticError(err_msg)

    return rtnval


def expand_ipv6_addr(addr: str) -> str:
    """
        Expands the ``::`` wildcard in an IPv6 address.

        :param addr: The IPv6 address to expand.

        :returns: The fully expanded IPv6 address.
    """
    expanded = addr

    # If we see '::' expand it, there should be only one
    double_colon_count = addr.count("::")
    if double_colon_count > 1:
        errmsg = f"Invalid IPv6 address which contains more than one wildcard '::'.  addr={addr}"
        raise ValueError(errmsg)
    elif double_colon_count == 1:
        before_colons, after_colons = addr.split("::")

        if before_colons == "":
            after_parts = after_colons.split(":")
            after_parts_len = len(after_parts)
            fill_part_count = 8 - after_parts_len
            fill_comp = [ nc for nc in '0' * fill_part_count ]
            expanded = ":".join(fill_comp) + ":" + after_colons

        elif after_colons == "":
            before_parts = before_colons.split(":")
            before_parts_len = len(before_parts)
            fill_part_count = 8 - before_parts_len
            fill_comp = [ nc for nc in '0' * fill_part_count ]
            expanded = before_colons + ":" + ":".join(fill_comp)

        else:
            after_parts = after_colons.split(":")
            after_parts_len = len(after_parts)
            before_parts = before_colons.split(":")
            before_parts_len = len(before_parts)

            fill_part_count = 8 - (after_parts_len + before_parts_len)
            fill_comp = [ nc for nc in '0' * fill_part_count ]
            expanded = before_colons + ":" + ":".join(fill_comp) + ":" + after_colons

    return expanded


def get_arp_table(normalize_hwaddr: bool=False):
    """
        Retrieves the ARP table from ``/proc/net/arp``.

        :param normalize_hwaddr: If ``True`` the hardware address is normalized by
            removing colons and converting to upper case.

        :returns: A dictionary keyed by hardware address with ARP table details.
    """
    arp_table = {}

    try:
        with open("/proc/net/arp", "r", encoding="utf-8") as aif:
            for line in aif.readlines()[1:]:  # skip header line
                fields = line.split()
                if len(fields) >= 6:
                    ip, hwtype, flags, hwaddr, mask, ifname = fields[:6]
                    if normalize_hwaddr:
                        hwaddr = hwaddr.replace(":", "").upper()
                    iinfo = {
                        hwaddr: {
                            "hwaddr": hwaddr,
                            "ip": ip,
                            "ifname": ifname,
                            "hwtype": hwtype,
                            "flags": flags,
                            "mask": mask,
                        }
                    }
                    arp_table.update(iinfo)
    except FileNotFoundError:
        # Non-Linux platforms may not expose '/proc/net/arp'
        pass

    return arp_table


def is_ipv4_address(candidate: str) -> bool:
    """
        Checks to see if ``candidate`` is an IPv4 address.

        :param candidate: A string that is to be checked to see if it is a valid IPv4 address.

        :returns: A boolean indicating if an IP address is an IPv4 address
    """
    is_ipv4 = False

    # The regex will ensure that all the component characters are integer characters
    # and that we have the correct number of components.
    mobj = REGEX_IPV4_COMPONENTS.match(candidate)
    if mobj is not None:
        addr_components = [ v for v in mobj.groups() ]
        if len(addr_components) == 4:
            is_ipv4 = True
            for nc in addr_components:
                cval = int(nc)
                if cval < 0 or cval > 255:
                    is_ipv4 = False
                    break

    return is_ipv4


def is_ipv6_address(candidate: str) -> bool:
    """
        Checks to see if ``candidate`` is an IPv6 address.

        :param candidate: A string that is to be checked to see if it is a valid IPv6 address.

        :returns: A boolean indicating if an IP address is an IPv6 address
    """
    is_ipv6 = False

    candidate = expand_ipv6_addr(candidate)
    
    # The regex will ensure that all the component characters are integer characters
    # and that we have the correct number of components.
    mobj = REGEX_IPV6_COMPONENTS.match(candidate)
    if mobj is not None:
        addr_components = [ v for v in mobj.groups() ]
        if len(addr_components) == 8:
            is_ipv6 = True
            for nc in addr_components:
                cval = int(nc, base=16)
                if cval < 0 or cval > 65535:
                    is_ipv6 = False
                    break

    return is_ipv6


def refresh_arp_table(
    exclude_interfaces: Optional[List[str]] = None,
    include_interfaces: Optional[List[str]] = None,
):
    """
        Refreshes the local ARP table by pinging hosts reachable from the
        specified network interfaces.

        :param exclude_interfaces: Interfaces that should not be scanned.
        :param include_interfaces: Optional list of specific interfaces to scan.

        :returns: ``None``
    """

    if exclude_interfaces is None:
        exclude_interfaces = ["lo"]

    interface_list = include_interfaces if include_interfaces is not None else netifaces.interfaces()
    
    for ifname in interface_list:
        if ifname not in exclude_interfaces:
            address_info = netifaces.ifaddresses(ifname)
            if address_info is not None:
                # Only attempt to refresh ARP using IPv4 addresses
                if netifaces.AF_INET in address_info:
                    for addr_info in address_info[netifaces.AF_INET]:
                        ifaddress = addr_info.get("addr")
                        if is_ipv4_address(ifaddress):
                            prefix = ".".join(ifaddress.split(".")[:-1])
                            ping_cmd = ARPING_RANGE_CMD % (prefix, prefix)
                            os.system(ping_cmd)

    return


if __name__ == "__main__":
    refresh_arp_table()
