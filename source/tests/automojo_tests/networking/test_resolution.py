import unittest
from unittest import mock
from io import StringIO

import netifaces

from automojo.networking import resolution


class ExpandIPv6AddrTests(unittest.TestCase):

    def test_expand_ipv6_with_leading_wildcard(self):
        expanded = resolution.expand_ipv6_addr("::1")
        self.assertEqual(expanded, "0:0:0:0:0:0:0:1")

    def test_expand_ipv6_with_trailing_wildcard(self):
        expanded = resolution.expand_ipv6_addr("fe80::")
        self.assertEqual(expanded, "fe80:0:0:0:0:0:0:0")

    def test_expand_ipv6_with_embedded_wildcard(self):
        expanded = resolution.expand_ipv6_addr("fe80::1")
        self.assertEqual(expanded, "fe80:0:0:0:0:0:0:1")

    def test_expand_ipv6_invalid_multiple_wildcards(self):
        with self.assertRaises(ValueError):
            resolution.expand_ipv6_addr("fe80::1::2")


class IPv4AddressTests(unittest.TestCase):

    def test_valid_ipv4_addresses(self):
        self.assertTrue(resolution.is_ipv4_address("127.0.0.1"))
        self.assertTrue(resolution.is_ipv4_address("255.255.255.255"))

    def test_invalid_ipv4_addresses(self):
        self.assertFalse(resolution.is_ipv4_address("256.0.0.1"))
        self.assertFalse(resolution.is_ipv4_address("abc.def.ghi.jkl"))


class IPv6AddressTests(unittest.TestCase):

    def test_valid_ipv6_addresses(self):
        self.assertTrue(resolution.is_ipv6_address("::1"))
        self.assertTrue(resolution.is_ipv6_address("fe80::1"))
        full_addr = "2001:0db8:85a3:0000:0000:8a2e:0370:7334"
        self.assertTrue(resolution.is_ipv6_address(full_addr))

    def test_invalid_ipv6_addresses(self):
        with self.assertRaises(ValueError):
            resolution.is_ipv6_address("fe80::1::2")
        self.assertFalse(resolution.is_ipv6_address("gggg::1"))


class GetArpTableTests(unittest.TestCase):

    def test_parse_arp_table_and_normalize(self):
        arp_data = (
            "IP address HW type Flags HW address Mask Device\n"
            "192.168.1.1 0x1 0x2 aa:bb:cc:dd:ee:ff * eth0\n"
            "10.0.0.1 0x1 0x2 11:22:33:44:55:66 * wlan0\n"
        )
        with mock.patch("builtins.open", return_value=StringIO(arp_data)):
            table = resolution.get_arp_table(normalize_hwaddr=True)
        self.assertIn("AABBCCDDEEFF", table)
        self.assertEqual(table["AABBCCDDEEFF"]["ip"], "192.168.1.1")
        self.assertIn("112233445566", table)

    def test_arp_table_file_missing(self):
        with mock.patch("builtins.open", side_effect=FileNotFoundError()):
            table = resolution.get_arp_table()
        self.assertEqual(table, {})


class RefreshArpTableTests(unittest.TestCase):

    def setUp(self):
        self.os_patcher = mock.patch("os.system")
        self.mock_os_system = self.os_patcher.start()
        self.ifaddrs_patcher = mock.patch("netifaces.ifaddresses")
        self.mock_ifaddresses = self.ifaddrs_patcher.start()
        self.interfaces_patcher = mock.patch("netifaces.interfaces", return_value=["eth0", "lo"])
        self.interfaces_patcher.start()

        self.mock_ifaddresses.return_value = {
            netifaces.AF_INET: [{"addr": "192.168.1.100"}]
        }

    def tearDown(self):
        self.os_patcher.stop()
        self.ifaddrs_patcher.stop()
        self.interfaces_patcher.stop()

    def test_refresh_arp_table_invokes_ping(self):
        resolution.refresh_arp_table()
        prefix = "192.168.1"
        expected_cmd = resolution.ARPING_RANGE_CMD % (prefix, prefix)
        self.mock_os_system.assert_called_with(expected_cmd)


if __name__ == "__main__":
    unittest.main()
