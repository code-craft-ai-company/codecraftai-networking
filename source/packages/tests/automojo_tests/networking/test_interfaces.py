import unittest
from unittest.mock import patch

import netifaces

from automojo.networking import interfaces


class TestInterfaces(unittest.TestCase):

    def test_get_ipv6_address_returns_ipv6_when_available(self):
        fake_addr = 'fe80::1'
        with patch('netifaces.ifaddresses') as mock_ifaddresses:
            mock_ifaddresses.return_value = {
                netifaces.AF_INET6: [{"addr": fake_addr}],
                netifaces.AF_INET: [{"addr": "127.0.0.1"}],
            }
            addr = interfaces.get_ipv6_address('eth0')
        self.assertEqual(addr, fake_addr)

    def test_get_correspondance_interface_none_when_no_ip(self):
        with patch('automojo.networking.interfaces.get_correspondance_ip_address', return_value=None) as gcia, \
             patch('automojo.networking.interfaces.get_interface_for_ip') as gifip:
            iface, ip = interfaces.get_correspondance_interface('1.1.1.1', 80)
            gcia.assert_called_once()
            gifip.assert_not_called()
        self.assertIsNone(ip)
        self.assertIsNone(iface)

    def test_get_correspondance_interface_returns_tuple_when_ip(self):
        with patch('automojo.networking.interfaces.get_correspondance_ip_address', return_value='1.2.3.4') as gcia, \
             patch('automojo.networking.interfaces.get_interface_for_ip', return_value='eth0') as gifip:
            iface, ip = interfaces.get_correspondance_interface('1.1.1.1', 80)
            gcia.assert_called_once()
            gifip.assert_called_once_with('1.2.3.4')
        self.assertEqual(ip, '1.2.3.4')
        self.assertEqual(iface, 'eth0')


if __name__ == '__main__':
    unittest.main()
