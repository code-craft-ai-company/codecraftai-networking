import unittest
from unittest import mock
import socket
import struct

from automojo.networking import unicast
from automojo.networking.constants import SO_RECV_ANYIF, IPPROTO_IPV6


class DummySocket:
    def __init__(self):
        self.options = []
        self.timeout = None
        self.bound = None

    def setsockopt(self, level, optname, value):
        self.options.append((level, optname, value))

    def settimeout(self, value):
        self.timeout = value

    def bind(self, addr):
        self.bound = addr


class CreateUnicastSocketTests(unittest.TestCase):
    def setUp(self):
        self.sock = DummySocket()
        self.patcher = mock.patch('socket.socket', return_value=self.sock)
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()

    def test_ipv4_ttl_sets_ip_ttl_option(self):
        ttl_val = 64
        result = unicast.create_unicast_socket('192.168.1.1', 5000, ttl=ttl_val)
        self.assertIs(result, self.sock)
        expected = (socket.IPPROTO_IP, socket.IP_TTL, struct.pack('B', ttl_val))
        self.assertIn(expected, self.sock.options)
        # ensure multicast specific options were not used
        for _, opt, _ in self.sock.options:
            self.assertNotIn(opt, [socket.IP_MULTICAST_IF,
                                   socket.IP_MULTICAST_TTL,
                                   socket.IP_MULTICAST_LOOP])

    def test_ipv6_ttl_sets_unicast_hops(self):
        ttl_val = 2
        result = unicast.create_unicast_socket('fe80::1', 5000,
                                                family=socket.AF_INET6,
                                                ttl=ttl_val,
                                                apple_p2p=True)
        self.assertIs(result, self.sock)
        self.assertIn((IPPROTO_IPV6, socket.IPV6_UNICAST_HOPS, ttl_val),
                      self.sock.options)
        self.assertIn((socket.SOL_SOCKET, SO_RECV_ANYIF, 1), self.sock.options)
        for _, opt, _ in self.sock.options:
            self.assertNotIn(opt, [socket.IPV6_MULTICAST_HOPS,
                                   socket.IPV6_MULTICAST_LOOP])


if __name__ == '__main__':
    unittest.main()
