"""
    .. module:: test_constants
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Unit tests for the :mod:`automojo.networking.constants` module.

    .. moduleauthor:: Automojo Test Author
"""

import re
import socket
import unittest

from automojo.networking import constants


class HttpProtocolConstantsTests(unittest.TestCase):
    """
        Verifies HTTP/1.1 protocol delimiter constants are defined and have
        the documented byte-string values.
    """

    def test_http1_1_linesep_value(self) -> None:
        """
            Verify the line separator constant equals ``\\r\\n``.
        """
        rtnval = constants.HTTP1_1_LINESEP
        self.assertEqual(rtnval, b"\r\n")
        return

    def test_http1_1_end_of_header_value(self) -> None:
        """
            Verify the end-of-header constant equals ``\\r\\n\\r\\n``.
        """
        rtnval = constants.HTTP1_1_END_OF_HEADER
        self.assertEqual(rtnval, b"\r\n\r\n")
        return

    def test_http1_1_end_of_message_value(self) -> None:
        """
            Verify the end-of-message constant equals ``\\r\\n\\r\\n``.
        """
        rtnval = constants.HTTP1_1_END_OF_MESSAGE
        self.assertEqual(rtnval, b"\r\n\r\n")
        return


class IPProtocolConstantsTests(unittest.TestCase):
    """
        Verifies platform fallback constants for IPPROTO_IPV6 and SO_RECV_ANYIF.
    """

    def test_ipproto_ipv6_is_int(self) -> None:
        """
            Verify ``IPPROTO_IPV6`` is an integer.
        """
        rtnval = constants.IPPROTO_IPV6
        self.assertIsInstance(rtnval, int)
        return

    def test_ipproto_ipv6_matches_socket_when_available(self) -> None:
        """
            When ``socket.IPPROTO_IPV6`` is available, the constant must equal it.
            Otherwise it falls back to 41.
        """
        if hasattr(socket, "IPPROTO_IPV6"):
            self.assertEqual(constants.IPPROTO_IPV6, socket.IPPROTO_IPV6)
        else:
            self.assertEqual(constants.IPPROTO_IPV6, 41)
        return

    def test_so_recv_anyif_is_int(self) -> None:
        """
            Verify ``SO_RECV_ANYIF`` is an integer.
        """
        rtnval = constants.SO_RECV_ANYIF
        self.assertIsInstance(rtnval, int)
        return

    def test_so_recv_anyif_fallback(self) -> None:
        """
            When ``socket.SO_RECV_ANYIF`` is unavailable, the fallback value is 0x1104.
        """
        if not hasattr(socket, "SO_RECV_ANYIF"):
            self.assertEqual(constants.SO_RECV_ANYIF, 0x1104)
        else:
            self.assertEqual(constants.SO_RECV_ANYIF, socket.SO_RECV_ANYIF)
        return


class MulticastAddressConstantsTests(unittest.TestCase):
    """
        Verifies the well-known multicast group constants and ports.
    """

    def test_mdns_group_addr_value(self) -> None:
        """
            Verify the IPv4 mDNS group address.
        """
        self.assertEqual(constants.MDNS_GROUP_ADDR, "224.0.0.251")
        return

    def test_mdns_group_addr6_value(self) -> None:
        """
            Verify the IPv6 mDNS group address.
        """
        self.assertEqual(constants.MDNS_GROUP_ADDR6, "ff02::fb")
        return

    def test_mdns_port_value(self) -> None:
        """
            Verify the mDNS port number.
        """
        self.assertEqual(constants.MDNS_PORT, 5353)
        return

    def test_upnp_group_addr_value(self) -> None:
        """
            Verify the IPv4 UPnP group address.
        """
        self.assertEqual(constants.UPNP_GROUP_ADDR, "239.255.255.250")
        return

    def test_upnp_ipv6_addresses(self) -> None:
        """
            Verify the IPv6 UPnP scoped group addresses.
        """
        self.assertEqual(constants.UPNP_GROUP_LOCAL_ADDR6, "FF02::1")
        self.assertEqual(constants.UPNP_GROUP_SITE_ADDR6, "FF05::1")
        self.assertEqual(constants.UPNP_GROUP_ORG_ADDR6, "FF08::1")
        self.assertEqual(constants.UPNP_GROUP_GLOBAL_ADDR6, "FF0E::1")
        return

    def test_upnp_port_value(self) -> None:
        """
            Verify the UPnP port number.
        """
        self.assertEqual(constants.UPNP_PORT, 1900)
        return

    def test_upnp_default_search_window_length(self) -> None:
        """
            Verify the UPnP default search window length.
        """
        self.assertEqual(constants.UPNP_DEFAULT_SEARCH_WINDOW_LENGTH, 20)
        return


class IpAddressRegexTests(unittest.TestCase):
    """
        Verifies the IPv4 and IPv6 component regex patterns are well-formed
        and capture the expected groups.
    """

    def test_ipv4_components_regex_matches_valid(self) -> None:
        """
            Verify the IPv4 regex captures four numeric components.
        """
        mobj = constants.REGEX_IPV4_COMPONENTS.match("192.168.1.42")
        self.assertIsNotNone(mobj)
        groups = mobj.groups()
        self.assertEqual(groups, ("192", "168", "1", "42"))
        return

    def test_ipv4_components_regex_rejects_text(self) -> None:
        """
            Verify the IPv4 regex rejects non-numeric input.
        """
        mobj = constants.REGEX_IPV4_COMPONENTS.match("abc.def.ghi.jkl")
        self.assertIsNone(mobj)
        return

    def test_ipv6_components_regex_matches_full(self) -> None:
        """
            Verify the IPv6 regex captures eight hex components on a fully
            expanded address.
        """
        addr = "2001:0db8:85a3:0000:0000:8a2e:0370:7334"
        mobj = constants.REGEX_IPV6_COMPONENTS.match(addr)
        self.assertIsNotNone(mobj)
        groups = mobj.groups()
        self.assertEqual(len(groups), 8)
        return

    def test_ipv6_components_regex_rejects_compressed(self) -> None:
        """
            The IPv6 component regex should NOT match a compressed ``::`` address;
            expansion happens upstream of the regex.
        """
        mobj = constants.REGEX_IPV6_COMPONENTS.match("fe80::1")
        self.assertIsNone(mobj)
        return

    def test_charset_ipv6_addr_value(self) -> None:
        """
            Verify the IPv6 character set string.
        """
        self.assertEqual(constants.CHARSET_IPV6_ADDR, "ABCDEFabcdef0123456789:")
        return

    def test_regex_objects_are_compiled(self) -> None:
        """
            Verify the regex constants are pre-compiled :class:`re.Pattern` objects.
        """
        self.assertIsInstance(constants.REGEX_IPV4_COMPONENTS, re.Pattern)
        self.assertIsInstance(constants.REGEX_IPV6_COMPONENTS, re.Pattern)
        return


class RegisteredMulticastAddressesTests(unittest.TestCase):
    """
        Spot-checks the :class:`RegisteredMulticastAddresses` IANA mapping class.
    """

    def test_base_address_value(self) -> None:
        """
            Verify the base multicast address.
        """
        self.assertEqual(
            constants.RegisteredMulticastAddresses.BASE,
            "224.0.0.0",
        )
        return

    def test_mdns_address_value(self) -> None:
        """
            Verify the IANA registered mDNS address.
        """
        self.assertEqual(
            constants.RegisteredMulticastAddresses.MDNS,
            "224.0.0.251",
        )
        return

    def test_all_systems_on_subnet_value(self) -> None:
        """
            Verify the all-systems-on-subnet address.
        """
        self.assertEqual(
            constants.RegisteredMulticastAddresses.ALL_SYSTEMS_ON_SUBNET,
            "224.0.0.1",
        )
        return

    def test_link_local_name_resolution_value(self) -> None:
        """
            Verify the link-local name resolution address.
        """
        self.assertEqual(
            constants.RegisteredMulticastAddresses.LINK_LOCAL_NAME_RESOLUTION,
            "224.0.0.252",
        )
        return


if __name__ == "__main__":
    unittest.main()
