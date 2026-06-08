"""
    .. module:: test_unicast
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Unit tests for the :mod:`ccai.networking.unicast` module.

    .. moduleauthor:: CodeCraftAI Test Author
"""

import socket
import struct
import unittest
from typing import List, Optional, Tuple
from unittest import mock

from ccai.networking import unicast
from ccai.networking.constants import IPPROTO_IPV6, SO_RECV_ANYIF


class FakeSocket:
    """
        Lightweight replacement for ``socket.socket`` that records configuration.
    """

    def __init__(self) -> None:
        """
            Initialize a :class:`FakeSocket` instance.
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


class CreateUnicastSocketIpv4Tests(unittest.TestCase):
    """
        Tests for :func:`unicast.create_unicast_socket` over IPv4.
    """

    def setUp(self) -> None:
        self.fake_sock = FakeSocket()
        self.patcher = mock.patch("socket.socket", return_value=self.fake_sock)
        self.mock_socket_factory = self.patcher.start()
        return

    def tearDown(self) -> None:
        self.patcher.stop()
        return

    def test_returns_the_created_socket(self) -> None:
        """
            Verify the returned object is the socket the factory produced.
        """
        rtnval = unicast.create_unicast_socket("192.168.1.1", 5000)
        self.assertIs(rtnval, self.fake_sock)
        return

    def test_sets_so_reuseaddr(self) -> None:
        """
            Verify ``SO_REUSEADDR`` is enabled on every socket.
        """
        unicast.create_unicast_socket("192.168.1.1", 5000)
        self.assertIn(
            (socket.SOL_SOCKET, socket.SO_REUSEADDR, 1), self.fake_sock.options
        )
        return

    def test_ttl_packs_as_byte_for_ipv4(self) -> None:
        """
            Verify ``ttl`` is packed as an unsigned byte on IPv4 sockets.
        """
        unicast.create_unicast_socket("192.168.1.1", 5000, ttl=64)
        expected = (socket.IPPROTO_IP, socket.IP_TTL, struct.pack("B", 64))
        self.assertIn(expected, self.fake_sock.options)
        return

    def test_does_not_set_multicast_options(self) -> None:
        """
            Verify multicast-specific socket options are never set on a unicast socket.
        """
        unicast.create_unicast_socket("192.168.1.1", 5000, ttl=32)
        forbidden = {
            socket.IP_MULTICAST_IF,
            socket.IP_MULTICAST_TTL,
            socket.IP_MULTICAST_LOOP,
        }
        for _, optname, _ in self.fake_sock.options:
            self.assertNotIn(optname, forbidden)
        return

    def test_binds_to_wildcard_with_specified_port(self) -> None:
        """
            Verify the socket binds to ``0.0.0.0`` with the requested port.
        """
        unicast.create_unicast_socket("192.168.1.1", 5000)
        self.assertEqual(self.fake_sock.bound, ("0.0.0.0", 5000))
        return

    def test_timeout_propagates_to_settimeout(self) -> None:
        """
            Verify a non-None ``timeout`` is forwarded to ``settimeout``.
        """
        unicast.create_unicast_socket("192.168.1.1", 5000, timeout=2.5)
        self.assertEqual(self.fake_sock.timeout, 2.5)
        return

    def test_apple_p2p_sets_so_recv_anyif(self) -> None:
        """
            Verify ``apple_p2p=True`` sets the SO_RECV_ANYIF option.
        """
        unicast.create_unicast_socket("192.168.1.1", 5000, apple_p2p=True)
        self.assertIn(
            (socket.SOL_SOCKET, SO_RECV_ANYIF, 1), self.fake_sock.options
        )
        return


class CreateUnicastSocketIpv6Tests(unittest.TestCase):
    """
        Tests for :func:`unicast.create_unicast_socket` over IPv6.
    """

    def setUp(self) -> None:
        self.fake_sock = FakeSocket()
        self.patcher = mock.patch("socket.socket", return_value=self.fake_sock)
        self.mock_socket_factory = self.patcher.start()
        return

    def tearDown(self) -> None:
        self.patcher.stop()
        return

    def test_ttl_sets_ipv6_unicast_hops(self) -> None:
        """
            Verify ``ttl`` is forwarded to ``IPV6_UNICAST_HOPS`` for IPv6 sockets.
        """
        unicast.create_unicast_socket(
            "fe80::1", 5000, family=socket.AF_INET6, ttl=2
        )
        self.assertIn(
            (IPPROTO_IPV6, socket.IPV6_UNICAST_HOPS, 2), self.fake_sock.options
        )
        return

    def test_does_not_set_multicast_hops_or_loop(self) -> None:
        """
            Verify multicast-specific IPv6 options are not set on a unicast socket.
        """
        unicast.create_unicast_socket(
            "fe80::1", 5000, family=socket.AF_INET6, ttl=2
        )
        forbidden = {socket.IPV6_MULTICAST_HOPS, socket.IPV6_MULTICAST_LOOP}
        for _, optname, _ in self.fake_sock.options:
            self.assertNotIn(optname, forbidden)
        return


class CreateUnicastSocketErrorTests(unittest.TestCase):
    """
        Tests for failure modes of :func:`unicast.create_unicast_socket`.
    """

    def test_unsupported_family_raises_runtime_error(self) -> None:
        """
            Verify an unsupported address family raises ``RuntimeError``.
        """
        with self.assertRaises(RuntimeError):
            unicast.create_unicast_socket("192.168.1.1", 5000, family=99)
        return


if __name__ == "__main__":
    unittest.main()
