"""
    .. module:: test_resolution
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Unit tests for the :mod:`ccai.networking.resolution` module.

    .. moduleauthor:: CodeCraftAI Test Author
"""

import unittest
from io import StringIO
import unittest.mock

import netifaces

from ccai.networking import resolution


class ExpandIpv6AddrTests(unittest.TestCase):
    """
        Tests for :func:`resolution.expand_ipv6_addr`.
    """

    def test_expand_with_leading_wildcard(self) -> None:
        """
            ``::1`` expands to a fully-qualified address.
        """
        rtnval = resolution.expand_ipv6_addr("::1")
        self.assertEqual(rtnval, "0:0:0:0:0:0:0:1")
        return

    def test_expand_with_trailing_wildcard(self) -> None:
        """
            ``fe80::`` expands to a fully-qualified address.
        """
        rtnval = resolution.expand_ipv6_addr("fe80::")
        self.assertEqual(rtnval, "fe80:0:0:0:0:0:0:0")
        return

    def test_expand_with_embedded_wildcard(self) -> None:
        """
            An address with an embedded ``::`` expands fully.
        """
        rtnval = resolution.expand_ipv6_addr("fe80::1")
        self.assertEqual(rtnval, "fe80:0:0:0:0:0:0:1")
        return

    def test_expand_passthrough_for_already_expanded_address(self) -> None:
        """
            Already-expanded addresses are returned unchanged.
        """
        addr = "2001:0db8:85a3:0000:0000:8a2e:0370:7334"
        rtnval = resolution.expand_ipv6_addr(addr)
        self.assertEqual(rtnval, addr)
        return

    def test_invalid_double_wildcard_raises_value_error(self) -> None:
        """
            Multiple ``::`` sequences should raise ``ValueError``.
        """
        with self.assertRaises(ValueError):
            resolution.expand_ipv6_addr("fe80::1::2")
        return


class IsIpv4AddressTests(unittest.TestCase):
    """
        Tests for :func:`resolution.is_ipv4_address`.
    """

    def test_valid_addresses_return_true(self) -> None:
        """
            Valid IPv4 strings produce ``True``.
        """
        self.assertTrue(resolution.is_ipv4_address("127.0.0.1"))
        self.assertTrue(resolution.is_ipv4_address("255.255.255.255"))
        self.assertTrue(resolution.is_ipv4_address("0.0.0.0"))
        return

    def test_out_of_range_components_return_false(self) -> None:
        """
            Components above 255 yield ``False``.
        """
        self.assertFalse(resolution.is_ipv4_address("256.0.0.1"))
        return

    def test_non_numeric_components_return_false(self) -> None:
        """
            Non-numeric components yield ``False``.
        """
        self.assertFalse(resolution.is_ipv4_address("abc.def.ghi.jkl"))
        return

    def test_wrong_component_count_returns_false(self) -> None:
        """
            Addresses with the wrong number of components yield ``False``.
        """
        self.assertFalse(resolution.is_ipv4_address("1.2.3"))
        self.assertFalse(resolution.is_ipv4_address("1.2.3.4.5"))
        return


class IsIpv6AddressTests(unittest.TestCase):
    """
        Tests for :func:`resolution.is_ipv6_address`.
    """

    def test_valid_addresses_return_true(self) -> None:
        """
            Valid IPv6 strings produce ``True``.
        """
        self.assertTrue(resolution.is_ipv6_address("::1"))
        self.assertTrue(resolution.is_ipv6_address("fe80::1"))
        full_addr = "2001:0db8:85a3:0000:0000:8a2e:0370:7334"
        self.assertTrue(resolution.is_ipv6_address(full_addr))
        return

    def test_invalid_hex_components_return_false(self) -> None:
        """
            Components containing non-hex characters yield ``False``.
        """
        self.assertFalse(resolution.is_ipv6_address("gggg::1"))
        return

    def test_double_wildcard_raises_value_error(self) -> None:
        """
            Multiple ``::`` sequences must raise from the underlying expand call.
        """
        with self.assertRaises(ValueError):
            resolution.is_ipv6_address("fe80::1::2")
        return


class GetArpTableTests(unittest.TestCase):
    """
        Tests for :func:`resolution.get_arp_table` (the ``/proc/net/arp`` reader).
    """

    def test_parses_proc_net_arp_table(self) -> None:
        """
            Verify a well-formed ``/proc/net/arp`` is parsed into a dictionary
            keyed by hardware address.
        """
        arp_data = (
            "IP address HW type Flags HW address Mask Device\n"
            "192.168.1.1 0x1 0x2 aa:bb:cc:dd:ee:ff * eth0\n"
            "10.0.0.1 0x1 0x2 11:22:33:44:55:66 * wlan0\n"
        )
        with unittest.mock.patch("builtins.open", return_value=StringIO(arp_data)):
            rtnval = resolution.get_arp_table()

        self.assertIn("aa:bb:cc:dd:ee:ff", rtnval)
        self.assertEqual(rtnval["aa:bb:cc:dd:ee:ff"]["ip"], "192.168.1.1")
        self.assertEqual(rtnval["aa:bb:cc:dd:ee:ff"]["ifname"], "eth0")
        self.assertIn("11:22:33:44:55:66", rtnval)
        return

    def test_normalize_hwaddr_strips_colons_and_uppercases(self) -> None:
        """
            Verify the ``normalize_hwaddr`` flag yields uppercase, colon-free keys.
        """
        arp_data = (
            "IP address HW type Flags HW address Mask Device\n"
            "192.168.1.1 0x1 0x2 aa:bb:cc:dd:ee:ff * eth0\n"
        )
        with unittest.mock.patch("builtins.open", return_value=StringIO(arp_data)):
            rtnval = resolution.get_arp_table(normalize_hwaddr=True)

        self.assertIn("AABBCCDDEEFF", rtnval)
        self.assertEqual(rtnval["AABBCCDDEEFF"]["ip"], "192.168.1.1")
        return

    def test_returns_empty_dict_when_proc_net_arp_missing(self) -> None:
        """
            Verify a missing ``/proc/net/arp`` (non-Linux) returns ``{}``.
        """
        with unittest.mock.patch("builtins.open", side_effect=FileNotFoundError()):
            rtnval = resolution.get_arp_table()
        self.assertEqual(rtnval, {})
        return

    def test_skips_lines_with_too_few_fields(self) -> None:
        """
            Verify malformed lines with fewer than 6 fields are skipped.
        """
        arp_data = (
            "IP address HW type Flags HW address Mask Device\n"
            "incomplete line\n"
            "192.168.1.1 0x1 0x2 aa:bb:cc:dd:ee:ff * eth0\n"
        )
        with unittest.mock.patch("builtins.open", return_value=StringIO(arp_data)):
            rtnval = resolution.get_arp_table()

        self.assertEqual(len(rtnval), 1)
        return


class RefreshArpTableTests(unittest.TestCase):
    """
        Tests for :func:`resolution.refresh_arp_table`.
    """

    def setUp(self) -> None:
        self.popen_patcher = unittest.mock.patch("ccai.networking.resolution.subprocess.Popen")
        self.mock_popen = self.popen_patcher.start()
        self.mock_popen.return_value = unittest.mock.MagicMock()
        self.ifaddrs_patcher = unittest.mock.patch("netifaces.ifaddresses")
        self.mock_ifaddresses = self.ifaddrs_patcher.start()
        self.interfaces_patcher = unittest.mock.patch(
            "netifaces.interfaces", return_value=["eth0", "lo"]
        )
        self.interfaces_patcher.start()

        self.mock_ifaddresses.return_value = {
            netifaces.AF_INET: [{"addr": "192.168.1.100"}]
        }
        return

    def tearDown(self) -> None:
        self.popen_patcher.stop()
        self.ifaddrs_patcher.stop()
        self.interfaces_patcher.stop()
        return

    def test_invokes_ping_for_eligible_interfaces(self) -> None:
        """
            Verify a ping sweep is invoked for the prefix of each non-excluded
            interface IPv4 address, each as a no-shell argv list.
        """
        resolution.refresh_arp_table()
        targets = [call.args[0][1] for call in self.mock_popen.call_args_list]
        self.assertTrue(any(t.startswith("192.168.1.") for t in targets))
        first_argv = self.mock_popen.call_args_list[0].args[0]
        self.assertEqual(first_argv[0], "ping")
        return

    def test_excludes_loopback_by_default(self) -> None:
        """
            Verify the default exclude list contains ``lo`` and prevents loopback
            from being scanned.
        """
        resolution.refresh_arp_table()
        for call_args in self.mock_popen.call_args_list:
            argv = call_args.args[0]
            self.assertNotIn("127.0", argv[1])
        return

    def test_include_interfaces_overrides_full_enumeration(self) -> None:
        """
            Verify supplying ``include_interfaces`` restricts the scan set.
        """
        resolution.refresh_arp_table(include_interfaces=["eth0"])
        self.assertGreaterEqual(self.mock_popen.call_count, 1)
        return

    def test_returns_none(self) -> None:
        """
            Verify the function returns ``None``.
        """
        rtnval = resolution.refresh_arp_table(include_interfaces=[])
        self.assertIsNone(rtnval)
        return


if __name__ == "__main__":
    unittest.main()
