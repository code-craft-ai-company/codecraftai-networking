"""
    .. module:: test_constants
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Testbase tests for the :mod:`ccai.networking.constants` module.

    .. moduleauthor:: CodeCraftAI Test Author
"""

import re
import socket

from ccai.networking import constants


def test_http1_1_linesep_value() -> None:
    """
        Verify the line separator constant equals ``\\r\\n``.
    """
    rtnval = constants.HTTP1_1_LINESEP
    assert rtnval == b"\r\n"
    return


def test_http1_1_end_of_header_value() -> None:
    """
        Verify the end-of-header constant equals ``\\r\\n\\r\\n``.
    """
    rtnval = constants.HTTP1_1_END_OF_HEADER
    assert rtnval == b"\r\n\r\n"
    return


def test_http1_1_end_of_message_value() -> None:
    """
        Verify the end-of-message constant equals ``\\r\\n\\r\\n``.
    """
    rtnval = constants.HTTP1_1_END_OF_MESSAGE
    assert rtnval == b"\r\n\r\n"
    return


def test_ipproto_ipv6_is_int() -> None:
    """
        Verify ``IPPROTO_IPV6`` is an integer.
    """
    rtnval = constants.IPPROTO_IPV6
    assert isinstance(rtnval, int)
    return


def test_ipproto_ipv6_matches_socket_when_available() -> None:
    """
        When ``socket.IPPROTO_IPV6`` is available, the constant must equal it.
        Otherwise it falls back to 41.
    """
    if hasattr(socket, "IPPROTO_IPV6"):
        assert constants.IPPROTO_IPV6 == socket.IPPROTO_IPV6
    else:
        assert constants.IPPROTO_IPV6 == 41
    return


def test_so_recv_anyif_is_int() -> None:
    """
        Verify ``SO_RECV_ANYIF`` is an integer.
    """
    rtnval = constants.SO_RECV_ANYIF
    assert isinstance(rtnval, int)
    return


def test_so_recv_anyif_fallback() -> None:
    """
        When ``socket.SO_RECV_ANYIF`` is unavailable, the fallback value is 0x1104.
    """
    if not hasattr(socket, "SO_RECV_ANYIF"):
        assert constants.SO_RECV_ANYIF == 0x1104
    else:
        assert constants.SO_RECV_ANYIF == socket.SO_RECV_ANYIF
    return


def test_mdns_group_addr_value() -> None:
    """
        Verify the IPv4 mDNS group address.
    """
    assert constants.MDNS_GROUP_ADDR == "224.0.0.251"
    return


def test_mdns_group_addr6_value() -> None:
    """
        Verify the IPv6 mDNS group address.
    """
    assert constants.MDNS_GROUP_ADDR6 == "ff02::fb"
    return


def test_mdns_port_value() -> None:
    """
        Verify the mDNS port number.
    """
    assert constants.MDNS_PORT == 5353
    return


def test_upnp_group_addr_value() -> None:
    """
        Verify the IPv4 UPnP group address.
    """
    assert constants.UPNP_GROUP_ADDR == "239.255.255.250"
    return


def test_upnp_ipv6_addresses() -> None:
    """
        Verify the IPv6 UPnP scoped group addresses.
    """
    assert constants.UPNP_GROUP_LOCAL_ADDR6 == "FF02::1"
    assert constants.UPNP_GROUP_SITE_ADDR6 == "FF05::1"
    assert constants.UPNP_GROUP_ORG_ADDR6 == "FF08::1"
    assert constants.UPNP_GROUP_GLOBAL_ADDR6 == "FF0E::1"
    return


def test_upnp_port_value() -> None:
    """
        Verify the UPnP port number.
    """
    assert constants.UPNP_PORT == 1900
    return


def test_upnp_default_search_window_length() -> None:
    """
        Verify the UPnP default search window length.
    """
    assert constants.UPNP_DEFAULT_SEARCH_WINDOW_LENGTH == 20
    return


def test_ipv4_components_regex_matches_valid() -> None:
    """
        Verify the IPv4 regex captures four numeric components.
    """
    mobj = constants.REGEX_IPV4_COMPONENTS.match("192.168.1.42")
    assert mobj is not None
    groups = mobj.groups()
    assert groups == ("192", "168", "1", "42")
    return


def test_ipv4_components_regex_rejects_text() -> None:
    """
        Verify the IPv4 regex rejects non-numeric input.
    """
    mobj = constants.REGEX_IPV4_COMPONENTS.match("abc.def.ghi.jkl")
    assert mobj is None
    return


def test_ipv6_components_regex_matches_full() -> None:
    """
        Verify the IPv6 regex captures eight hex components on a fully
        expanded address.
    """
    addr = "2001:0db8:85a3:0000:0000:8a2e:0370:7334"
    mobj = constants.REGEX_IPV6_COMPONENTS.match(addr)
    assert mobj is not None
    groups = mobj.groups()
    assert len(groups) == 8
    return


def test_ipv6_components_regex_rejects_compressed() -> None:
    """
        The IPv6 component regex should NOT match a compressed ``::`` address;
        expansion happens upstream of the regex.
    """
    mobj = constants.REGEX_IPV6_COMPONENTS.match("fe80::1")
    assert mobj is None
    return


def test_charset_ipv6_addr_value() -> None:
    """
        Verify the IPv6 character set string.
    """
    assert constants.CHARSET_IPV6_ADDR == "ABCDEFabcdef0123456789:"
    return


def test_regex_objects_are_compiled() -> None:
    """
        Verify the regex constants are pre-compiled :class:`re.Pattern` objects.
    """
    assert isinstance(constants.REGEX_IPV4_COMPONENTS, re.Pattern)
    assert isinstance(constants.REGEX_IPV6_COMPONENTS, re.Pattern)
    return


def test_base_address_value() -> None:
    """
        Verify the base multicast address.
    """
    assert constants.RegisteredMulticastAddresses.BASE == "224.0.0.0"
    return


def test_mdns_address_value() -> None:
    """
        Verify the IANA registered mDNS address.
    """
    assert constants.RegisteredMulticastAddresses.MDNS == "224.0.0.251"
    return


def test_all_systems_on_subnet_value() -> None:
    """
        Verify the all-systems-on-subnet address.
    """
    assert constants.RegisteredMulticastAddresses.ALL_SYSTEMS_ON_SUBNET == "224.0.0.1"
    return


def test_link_local_name_resolution_value() -> None:
    """
        Verify the link-local name resolution address.
    """
    assert constants.RegisteredMulticastAddresses.LINK_LOCAL_NAME_RESOLUTION == "224.0.0.252"
    return
