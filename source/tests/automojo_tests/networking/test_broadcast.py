import socket
import unittest
from unittest import mock

from automojo.networking import broadcast


class BroadcastWakeOnLanTests(unittest.TestCase):

    def setUp(self):
        self.dummy_socket = DummySocket()
        self.patcher = mock.patch("socket.socket", return_value=self.dummy_socket)
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()

    def test_invalid_mac_address_raises_value_error(self):
        with self.assertRaises(ValueError):
            broadcast.broadcast_wake_on_lan_magic_message('255.255.255.255', '00:00:00:00:00')

    def test_magic_packet_sent_to_broadcast_address(self):
        broadcast.broadcast_wake_on_lan_magic_message('255.255.255.255', 'AA:BB:CC:DD:EE:FF')
        self.assertEqual(self.dummy_socket.sent_addr, ('255.255.255.255', 9))
        # Magic packet should be 102 bytes (6 FF bytes + 16 repetitions of MAC)
        self.assertEqual(len(self.dummy_socket.sent_data), 102)

    def test_dash_delimited_mac_is_supported(self):
        broadcast.broadcast_wake_on_lan_magic_message('255.255.255.255', 'AA-BB-CC-DD-EE-FF')
        self.assertEqual(self.dummy_socket.sent_addr, ('255.255.255.255', 9))
        self.assertEqual(len(self.dummy_socket.sent_data), 102)

    def test_setsockopt_called_for_broadcast(self):
        broadcast.broadcast_wake_on_lan_magic_message('255.255.255.255', 'AA:BB:CC:DD:EE:FF')
        self.assertEqual(self.dummy_socket.setsockopt_args, (socket.SOL_SOCKET, socket.SO_BROADCAST, 1))

    def test_socket_is_closed_after_use(self):
        broadcast.broadcast_wake_on_lan_magic_message('255.255.255.255', 'AA:BB:CC:DD:EE:FF')
        self.assertTrue(self.dummy_socket.closed)


class DummySocket:
    def __init__(self):
        self.sent_data = None
        self.sent_addr = None
        self.setsockopt_args = None
        self.closed = False

    def setsockopt(self, *args, **kwargs):
        self.setsockopt_args = args

    def sendto(self, data, addr):
        self.sent_data = data
        self.sent_addr = addr

    def close(self):
        self.closed = True


if __name__ == '__main__':
    unittest.main()
