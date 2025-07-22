import unittest
from unittest import mock

import netifaces

from automojo.networking import interfaces


class GetAllIPv4InterfacesTests(unittest.TestCase):

    def setUp(self):
        self.ifnames = ["eth0", "lo", "wlan0"]
        self.interfaces_patcher = mock.patch("netifaces.interfaces", return_value=self.ifnames)
        self.mock_interfaces = self.interfaces_patcher.start()

        addr_map = {
            "eth0": {netifaces.AF_INET: [{"addr": "192.168.1.10"}]},
            "lo": {netifaces.AF_INET: [{"addr": "127.0.0.1"}]},
            "wlan0": {netifaces.AF_INET6: [{"addr": "fe80::1"}]}
        }

        def fake_ifaddresses(ifname):
            return addr_map.get(ifname, {})

        self.ifaddresses_patcher = mock.patch("netifaces.ifaddresses", side_effect=fake_ifaddresses)
        self.mock_ifaddresses = self.ifaddresses_patcher.start()

    def tearDown(self):
        self.interfaces_patcher.stop()
        self.ifaddresses_patcher.stop()

    def test_returns_only_ipv4_interfaces(self):
        expected = ["eth0", "lo"]
        result = interfaces.get_all_ipv4_interfaces()
        self.assertEqual(result, expected)

    def test_returns_empty_list_when_no_ipv4(self):
        self.interfaces_patcher.stop()
        self.ifaddresses_patcher.stop()

        self.interfaces_patcher = mock.patch("netifaces.interfaces", return_value=self.ifnames)
        self.interfaces_patcher.start()

        def fake_no_ipv4(ifname):
            return {netifaces.AF_INET6: [{"addr": "fe80::1"}]}

        self.ifaddresses_patcher = mock.patch("netifaces.ifaddresses", side_effect=fake_no_ipv4)
        self.ifaddresses_patcher.start()

        result = interfaces.get_all_ipv4_interfaces()
        self.assertEqual(result, [])


class GetAllIPv6InterfacesTests(unittest.TestCase):

    def setUp(self):
        self.ifnames = ["eth0", "lo", "wlan0"]
        self.interfaces_patcher = mock.patch("netifaces.interfaces", return_value=self.ifnames)
        self.interfaces_patcher.start()

        addr_map = {
            "eth0": {
                netifaces.AF_INET: [{"addr": "192.168.1.10"}],
                netifaces.AF_INET6: [{"addr": "fe80::1"}]
            },
            "lo": {netifaces.AF_INET: [{"addr": "127.0.0.1"}]},
            "wlan0": {netifaces.AF_INET6: [{"addr": "fe80::2"}]}
        }

        def fake_ifaddresses(ifname):
            return addr_map.get(ifname, {})

        self.ifaddresses_patcher = mock.patch("netifaces.ifaddresses", side_effect=fake_ifaddresses)
        self.ifaddresses_patcher.start()

    def tearDown(self):
        self.interfaces_patcher.stop()
        self.ifaddresses_patcher.stop()

    def test_returns_only_ipv6_interfaces(self):
        expected = ["eth0", "wlan0"]
        result = interfaces.get_all_ipv6_interfaces()
        self.assertEqual(result, expected)

    def test_returns_empty_list_when_no_ipv6(self):
        self.interfaces_patcher.stop()
        self.ifaddresses_patcher.stop()

        self.interfaces_patcher = mock.patch("netifaces.interfaces", return_value=self.ifnames)
        self.interfaces_patcher.start()

        def fake_no_ipv6(ifname):
            return {netifaces.AF_INET: [{"addr": "10.0.0.1"}]}

        self.ifaddresses_patcher = mock.patch("netifaces.ifaddresses", side_effect=fake_no_ipv6)
        self.ifaddresses_patcher.start()

        result = interfaces.get_all_ipv6_interfaces()
        self.assertEqual(result, [])


if __name__ == "__main__":
    unittest.main()
