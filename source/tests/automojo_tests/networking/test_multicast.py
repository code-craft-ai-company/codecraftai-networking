import struct
import unittest
from unittest import mock
import socket

from automojo.networking import multicast
from automojo.networking.constants import IPPROTO_IPV6, SO_RECV_ANYIF


class DummySocket:
    def __init__(self):
        self.options = []
        self.bound = None
        self.timeout = None

    def setsockopt(self, *args):
        self.options.append(args)

    def bind(self, addr):
        self.bound = addr

    def settimeout(self, timeout):
        self.timeout = timeout

    def close(self):
        pass


class MulticastListenerSocketTests(unittest.TestCase):
    def setUp(self):
        self.dummy_socket = DummySocket()
        self.patcher = mock.patch('socket.socket', return_value=self.dummy_socket)
        self.mock_socket = self.patcher.start()
        self.ifname_patch = mock.patch('socket.if_nametoindex', return_value=2)
        self.ifname_patch.start()

    def tearDown(self):
        self.patcher.stop()
        self.ifname_patch.stop()

    def test_create_listener_socket_ipv4(self):
        sock = multicast.create_multicast_listener_socket(
            '224.0.0.1', 1900,
            bind_addr='1.2.3.4', family=socket.AF_INET,
            ttl=2, loop=1, timeout=5, apple_p2p=True
        )

        self.mock_socket.assert_called_with(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)

        membership = socket.inet_aton('224.0.0.1') + socket.inet_aton('1.2.3.4')
        self.assertIn((socket.SOL_SOCKET, socket.SO_REUSEADDR, 1), self.dummy_socket.options)
        self.assertIn((socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, membership), self.dummy_socket.options)
        self.assertIn((socket.SOL_SOCKET, SO_RECV_ANYIF, 1), self.dummy_socket.options)
        self.assertIn((socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, struct.pack('B', 2)), self.dummy_socket.options)
        self.assertIn((socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, struct.pack('b', 1)), self.dummy_socket.options)
        self.assertEqual(self.dummy_socket.bound, ('1.2.3.4', 1900))
        self.assertEqual(self.dummy_socket.timeout, 5)
        self.assertIs(sock, self.dummy_socket)

    def test_create_listener_socket_ipv6(self):
        sock = multicast.create_multicast_listener_socket(
            'ff02::1', 1900,
            bind_addr='::', family=socket.AF_INET6,
            ttl=1, loop=0, timeout=2, apple_p2p=True
        )

        self.mock_socket.assert_called_with(socket.AF_INET6, socket.SOCK_DGRAM, socket.IPPROTO_UDP)

        mreq = socket.inet_pton(socket.AF_INET6, 'ff02::1') + struct.pack('@I', 0)
        self.assertIn((socket.SOL_SOCKET, socket.SO_REUSEADDR, 1), self.dummy_socket.options)
        self.assertIn((IPPROTO_IPV6, socket.IPV6_JOIN_GROUP, mreq), self.dummy_socket.options)
        self.assertIn((socket.SOL_SOCKET, SO_RECV_ANYIF, 1), self.dummy_socket.options)
        self.assertIn((IPPROTO_IPV6, socket.IPV6_MULTICAST_HOPS, 1), self.dummy_socket.options)
        self.assertIn((IPPROTO_IPV6, socket.IPV6_MULTICAST_LOOP, 0), self.dummy_socket.options)
        self.assertEqual(self.dummy_socket.bound, ('::', 1900))
        self.assertEqual(self.dummy_socket.timeout, 2)
        self.assertIs(sock, self.dummy_socket)

    def test_create_listener_socket_for_iface_ipv4(self):
        get_ipv4_patch = mock.patch('automojo.networking.multicast.get_ipv4_address', return_value='192.168.0.10')
        with get_ipv4_patch:
            sock = multicast.create_multicast_listener_socket_for_iface(
                'eth0', '224.0.0.1', 1900, family=socket.AF_INET
            )

        self.mock_socket.assert_called_with(socket.AF_INET, socket.SOCK_DGRAM)
        iface_opt = (socket.IPPROTO_IP, socket.IP_MULTICAST_IF, socket.inet_aton('192.168.0.10'))
        membership = socket.inet_aton('224.0.0.1') + socket.inet_aton('192.168.0.10')
        self.assertIn(iface_opt, self.dummy_socket.options)
        self.assertIn((socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, membership), self.dummy_socket.options)
        self.assertIs(sock, self.dummy_socket)

    def test_create_listener_socket_for_iface_ipv6(self):
        with mock.patch('automojo.networking.multicast.get_ipv6_address', return_value='fe80::1'), \
             mock.patch('automojo.networking.multicast.socket.inet_aton', return_value=b'\x00' * 4):
            sock = multicast.create_multicast_listener_socket_for_iface(
                'eth0', 'ff02::1', 1900, family=socket.AF_INET6
            )

        self.mock_socket.assert_called_with(socket.AF_INET6, socket.SOCK_DGRAM)
        iface_opt = (socket.IPPROTO_IP, socket.IP_MULTICAST_IF, b'\x00' * 4)
        mreq = socket.inet_pton(socket.AF_INET6, 'ff02::1') + struct.pack('@I', 2)
        self.assertIn(iface_opt, self.dummy_socket.options)
        self.assertIn((IPPROTO_IPV6, socket.IPV6_JOIN_GROUP, mreq), self.dummy_socket.options)
        self.assertIs(sock, self.dummy_socket)


if __name__ == '__main__':
    unittest.main()
