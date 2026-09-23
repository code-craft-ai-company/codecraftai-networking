"""
    .. module:: test_multicast
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Unit tests for the :mod:`ccai.networking.multicast` module.

    .. moduleauthor:: CodeCraftAI Test Author
"""

import socket
import struct
import unittest
from typing import List, Optional, Tuple
import unittest.mock

from ccai.networking import multicast
from ccai.networking.constants import IPPROTO_IPV6, SO_RECV_ANYIF


class FakeSocket:
    """
        Lightweight replacement for ``socket.socket`` that records its options
        and the bind address.
    """

    def __init__(self) -> None:
        """
            Initialize a :class:`FakeSocket`.
        """
        self.options: List[Tuple[int, int, object]] = []
        self.timeout: Optional[float] = None
        self.bound: Optional[Tuple[str, int]] = None
        self.closed: bool = False
        return

    def setsockopt(self, level: int, optname: int, value: object) -> None:
        """
            Record a setsockopt call.
        """
        self.options.append((level, optname, value))
        return

    def settimeout(self, value: float) -> None:
        """
            Record the configured timeout.
        """
        self.timeout = value
        return

    def bind(self, addr: Tuple[str, int]) -> None:
        """
            Record the bind address.
        """
        self.bound = addr
        return

    def close(self) -> None:
        """
            Record close.
        """
        self.closed = True
        return


class MulticastListenerSocketIpv4Tests(unittest.TestCase):
    """
        Tests for :func:`multicast.create_multicast_listener_socket` over IPv4.
    """

    def setUp(self) -> None:
        self.fake_sock = FakeSocket()
        self.socket_patcher = unittest.mock.patch("socket.socket", return_value=self.fake_sock)
        self.mock_socket = self.socket_patcher.start()
        return

    def tearDown(self) -> None:
        self.socket_patcher.stop()
        return

    def test_creates_udp_socket_with_correct_family(self) -> None:
        """
            Verify the socket is created as AF_INET, SOCK_DGRAM, IPPROTO_UDP.
        """
        multicast.create_multicast_listener_socket(
            "224.0.0.1", 1900, family=socket.AF_INET
        )
        self.mock_socket.assert_called_with(
            socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP
        )
        return

    def test_full_option_set_for_ipv4_listener(self) -> None:
        """
            Verify all socket options and the bind address are configured for
            an IPv4 listener.
        """
        rtnval = multicast.create_multicast_listener_socket(
            "224.0.0.1",
            1900,
            bind_addr="1.2.3.4",
            family=socket.AF_INET,
            ttl=2,
            loop=1,
            timeout=5,
            apple_p2p=True,
        )

        membership = socket.inet_aton("224.0.0.1") + socket.inet_aton("1.2.3.4")
        self.assertIn(
            (socket.SOL_SOCKET, socket.SO_REUSEADDR, 1), self.fake_sock.options
        )
        self.assertIn(
            (socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, membership),
            self.fake_sock.options,
        )
        self.assertIn(
            (socket.SOL_SOCKET, SO_RECV_ANYIF, 1), self.fake_sock.options
        )
        self.assertIn(
            (socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, struct.pack("B", 2)),
            self.fake_sock.options,
        )
        self.assertIn(
            (socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, struct.pack("b", 1)),
            self.fake_sock.options,
        )
        self.assertEqual(self.fake_sock.bound, ("1.2.3.4", 1900))
        self.assertEqual(self.fake_sock.timeout, 5)
        self.assertIs(rtnval, self.fake_sock)
        return

    def test_no_ttl_option_when_ttl_omitted(self) -> None:
        """
            Verify the TTL option is not set when no TTL is supplied.
        """
        multicast.create_multicast_listener_socket(
            "224.0.0.1", 1900, bind_addr="0.0.0.0", family=socket.AF_INET
        )
        for _, optname, _ in self.fake_sock.options:
            self.assertNotEqual(optname, socket.IP_MULTICAST_TTL)
        return


class MulticastListenerSocketIpv6Tests(unittest.TestCase):
    """
        Tests for :func:`multicast.create_multicast_listener_socket` over IPv6.
    """

    def setUp(self) -> None:
        self.fake_sock = FakeSocket()
        self.socket_patcher = unittest.mock.patch("socket.socket", return_value=self.fake_sock)
        self.mock_socket = self.socket_patcher.start()
        return

    def tearDown(self) -> None:
        self.socket_patcher.stop()
        return

    def test_full_option_set_for_ipv6_listener(self) -> None:
        """
            Verify all socket options and the bind address are configured for
            an IPv6 listener.
        """
        rtnval = multicast.create_multicast_listener_socket(
            "ff02::1",
            1900,
            bind_addr="::",
            family=socket.AF_INET6,
            ttl=1,
            loop=0,
            timeout=2,
            apple_p2p=True,
        )

        mreq = socket.inet_pton(socket.AF_INET6, "ff02::1") + struct.pack("@I", 0)
        self.assertIn(
            (socket.SOL_SOCKET, socket.SO_REUSEADDR, 1), self.fake_sock.options
        )
        self.assertIn(
            (IPPROTO_IPV6, socket.IPV6_JOIN_GROUP, mreq), self.fake_sock.options
        )
        self.assertIn(
            (socket.SOL_SOCKET, SO_RECV_ANYIF, 1), self.fake_sock.options
        )
        self.assertIn(
            (IPPROTO_IPV6, socket.IPV6_MULTICAST_HOPS, 1), self.fake_sock.options
        )
        self.assertIn(
            (IPPROTO_IPV6, socket.IPV6_MULTICAST_LOOP, 0), self.fake_sock.options
        )
        self.assertEqual(self.fake_sock.bound, ("::", 1900))
        self.assertEqual(self.fake_sock.timeout, 2)
        self.assertIs(rtnval, self.fake_sock)
        return


class MulticastListenerSocketErrorTests(unittest.TestCase):
    """
        Tests for failure modes of :func:`multicast.create_multicast_listener_socket`.
    """

    def test_unsupported_family_raises_runtime_error(self) -> None:
        """
            Verify an unsupported family raises ``RuntimeError``.
        """
        with self.assertRaises(RuntimeError):
            multicast.create_multicast_listener_socket(
                "224.0.0.1", 1900, family=99
            )
        return


class MulticastListenerSocketForIfaceTests(unittest.TestCase):
    """
        Tests for :func:`multicast.create_multicast_listener_socket_for_iface`.
    """

    def setUp(self) -> None:
        self.fake_sock = FakeSocket()
        self.socket_patcher = unittest.mock.patch("socket.socket", return_value=self.fake_sock)
        self.mock_socket = self.socket_patcher.start()
        self.if_index_patcher = unittest.mock.patch(
            "socket.if_nametoindex", return_value=2
        )
        self.if_index_patcher.start()
        return

    def tearDown(self) -> None:
        self.socket_patcher.stop()
        self.if_index_patcher.stop()
        return

    def test_ipv4_iface_socket_sets_multicast_if_and_membership(self) -> None:
        """
            Verify the IPv4 per-interface listener sets ``IP_MULTICAST_IF`` and
            joins the multicast group with the interface IP.
        """
        with unittest.mock.patch(
            "ccai.networking.multicast.get_ipv4_address",
            return_value="192.168.0.10",
        ):
            rtnval = multicast.create_multicast_listener_socket_for_iface(
                "eth0", "224.0.0.1", 1900, family=socket.AF_INET
            )

        self.mock_socket.assert_called_with(socket.AF_INET, socket.SOCK_DGRAM)
        iface_opt = (
            socket.IPPROTO_IP,
            socket.IP_MULTICAST_IF,
            socket.inet_aton("192.168.0.10"),
        )
        membership = (
            socket.inet_aton("224.0.0.1") + socket.inet_aton("192.168.0.10")
        )
        self.assertIn(iface_opt, self.fake_sock.options)
        self.assertIn(
            (socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, membership),
            self.fake_sock.options,
        )
        self.assertIs(rtnval, self.fake_sock)
        return

    def test_ipv6_iface_socket_uses_interface_index(self) -> None:
        """
            Verify the IPv6 per-interface listener resolves the interface
            index and joins the IPv6 multicast group.
        """
        with unittest.mock.patch(
            "ccai.networking.multicast.get_ipv6_address",
            return_value="fe80::1",
        ), unittest.mock.patch(
            "ccai.networking.multicast.socket.inet_aton",
            return_value=b"\x00" * 4,
        ):
            rtnval = multicast.create_multicast_listener_socket_for_iface(
                "eth0", "ff02::1", 1900, family=socket.AF_INET6
            )

        self.mock_socket.assert_called_with(socket.AF_INET6, socket.SOCK_DGRAM)
        mreq = socket.inet_pton(socket.AF_INET6, "ff02::1") + struct.pack("@I", 2)
        self.assertIn(
            (IPPROTO_IPV6, socket.IPV6_JOIN_GROUP, mreq),
            self.fake_sock.options,
        )
        self.assertIs(rtnval, self.fake_sock)
        return

    def test_unsupported_family_raises_runtime_error(self) -> None:
        """
            Verify an unsupported family raises ``RuntimeError``.
        """
        with self.assertRaises(RuntimeError):
            multicast.create_multicast_listener_socket_for_iface(
                "eth0", "224.0.0.1", 1900, family=99
            )
        return


if __name__ == "__main__":
    unittest.main()
