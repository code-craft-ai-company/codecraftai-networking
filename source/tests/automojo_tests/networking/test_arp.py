import unittest
from unittest.mock import patch

from automojo.networking import arp


class TestGetArpTable(unittest.TestCase):

    def test_get_arp_table_windows(self):
        windows_output = (
            "Interface: 192.168.1.2 --- 0x3\n"
            "  Internet Address      Physical Address      Type\n"
            "  192.168.1.1           00-1D-A1-B1-C5-DF     dynamic\n"
            "  10.0.0.1              5c-bd-e2-2e-a3-25     dynamic\n"
        )

        with patch('platform.system', return_value='Windows'):
            with patch('subprocess.check_output', return_value=windows_output):
                table = arp.get_arp_table()

        expected = [
            {'IPAddress': '192.168.1.1', 'HWType': 'dynamic', 'MACAddress': '00-1D-A1-B1-C5-DF'},
            {'IPAddress': '10.0.0.1', 'HWType': 'dynamic', 'MACAddress': '5c-bd-e2-2e-a3-25'}
        ]
        self.assertEqual(table, expected)

    def test_get_arp_table_linux(self):
        linux_output = (
            "192.168.1.1 dev eth0 lladdr 00:1d:a1:b1:c5:df REACHABLE\n"
            "10.0.0.1 dev wlan0 lladdr 5c:bd:e2:2e:a3:25 STALE\n"
        )

        with patch('platform.system', return_value='Linux'):
            with patch('subprocess.check_output', return_value=linux_output):
                table = arp.get_arp_table()

        expected = [
            {'IPAddress': '192.168.1.1', 'HWType': 'eth0', 'MACAddress': '00:1d:a1:b1:c5:df'},
            {'IPAddress': '10.0.0.1', 'HWType': 'wlan0', 'MACAddress': '5c:bd:e2:2e:a3:25'}
        ]
        self.assertEqual(table, expected)


if __name__ == '__main__':
    unittest.main()
