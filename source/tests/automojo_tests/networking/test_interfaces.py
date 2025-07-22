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


class TestInterfaces(unittest.TestCase):

    def test_get_ipv6_address_returns_ipv6_when_available(self):
        fake_addr = 'fe80::1'
        with mock.patch('netifaces.ifaddresses') as mock_ifaddresses:
            mock_ifaddresses.return_value = {
                netifaces.AF_INET6: [{"addr": fake_addr}],
                netifaces.AF_INET: [{"addr": "127.0.0.1"}],
            }
            addr = interfaces.get_ipv6_address('eth0')
        self.assertEqual(addr, fake_addr)

    def test_get_correspondance_interface_none_when_no_ip(self):
        with mock.patch('automojo.networking.interfaces.get_correspondance_ip_address', return_value=None) as gcia, \
             mock.patch('automojo.networking.interfaces.get_interface_for_ip') as gifip:
            iface, ip = interfaces.get_correspondance_interface('1.1.1.1', 80)
            gcia.assert_called_once()
            gifip.assert_not_called()
        self.assertIsNone(ip)
        self.assertIsNone(iface)

    def test_get_correspondance_interface_returns_tuple_when_ip(self):
        with mock.patch('automojo.networking.interfaces.get_correspondance_ip_address', return_value='1.2.3.4') as gcia, \
             mock.patch('automojo.networking.interfaces.get_interface_for_ip', return_value='eth0') as gifip:
            iface, ip = interfaces.get_correspondance_interface('1.1.1.1', 80)
            gcia.assert_called_once()
            gifip.assert_called_once_with('1.2.3.4')
        self.assertEqual(ip, '1.2.3.4')
        self.assertEqual(iface, 'eth0')


if __name__ == '__main__':
    unittest.main()
