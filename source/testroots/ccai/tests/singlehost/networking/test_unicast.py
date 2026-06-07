"""
    .. module:: test_unicast
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Testbase tests for the :mod:`ccai.networking.unicast` module.

    .. moduleauthor:: CodeCraftAI Test Author
"""

import socket
import struct
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


def _establish_env() -> Tuple[FakeSocket, object]:
    """
        Replicate the per-test setUp shared by the IPv4 and IPv6 unicast socket
        test cases: create a :class:`FakeSocket` and start a ``mock.patch`` that
        makes ``socket.socket`` return it.

        :returns: A tuple of the :class:`FakeSocket` instance and the active
                  patcher (so the caller can stop it during teardown).
    """
    fake_sock = FakeSocket()
    patcher = mock.patch("socket.socket", return_value=fake_sock)
    patcher.start()
    rtnval = (fake_sock, patcher)
    return rtnval


def test_returns_the_created_socket() -> None:
    """
        Verify the returned object is the socket the factory produced.
    """
    fake_sock, patcher = _establish_env()
    try:
        rtnval = unicast.create_unicast_socket("192.168.1.1", 5000)
        assert rtnval is fake_sock
    finally:
        patcher.stop()
    return


def test_sets_so_reuseaddr() -> None:
    """
        Verify ``SO_REUSEADDR`` is enabled on every socket.
    """
    fake_sock, patcher = _establish_env()
    try:
        unicast.create_unicast_socket("192.168.1.1", 5000)
        assert (socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) in fake_sock.options
    finally:
        patcher.stop()
    return


def test_ttl_packs_as_byte_for_ipv4() -> None:
    """
        Verify ``ttl`` is packed as an unsigned byte on IPv4 sockets.
    """
    fake_sock, patcher = _establish_env()
    try:
        unicast.create_unicast_socket("192.168.1.1", 5000, ttl=64)
        expected = (socket.IPPROTO_IP, socket.IP_TTL, struct.pack("B", 64))
        assert expected in fake_sock.options
    finally:
        patcher.stop()
    return


def test_does_not_set_multicast_options() -> None:
    """
        Verify multicast-specific socket options are never set on a unicast socket.
    """
    fake_sock, patcher = _establish_env()
    try:
        unicast.create_unicast_socket("192.168.1.1", 5000, ttl=32)
        forbidden = {
            socket.IP_MULTICAST_IF,
            socket.IP_MULTICAST_TTL,
            socket.IP_MULTICAST_LOOP,
        }
        for _, optname, _ in fake_sock.options:
            assert optname not in forbidden
    finally:
        patcher.stop()
    return


def test_binds_to_wildcard_with_specified_port() -> None:
    """
        Verify the socket binds to ``0.0.0.0`` with the requested port.
    """
    fake_sock, patcher = _establish_env()
    try:
        unicast.create_unicast_socket("192.168.1.1", 5000)
        assert fake_sock.bound == ("0.0.0.0", 5000)
    finally:
        patcher.stop()
    return


def test_timeout_propagates_to_settimeout() -> None:
    """
        Verify a non-None ``timeout`` is forwarded to ``settimeout``.
    """
    fake_sock, patcher = _establish_env()
    try:
        unicast.create_unicast_socket("192.168.1.1", 5000, timeout=2.5)
        assert fake_sock.timeout == 2.5
    finally:
        patcher.stop()
    return


def test_apple_p2p_sets_so_recv_anyif() -> None:
    """
        Verify ``apple_p2p=True`` sets the SO_RECV_ANYIF option.
    """
    fake_sock, patcher = _establish_env()
    try:
        unicast.create_unicast_socket("192.168.1.1", 5000, apple_p2p=True)
        assert (socket.SOL_SOCKET, SO_RECV_ANYIF, 1) in fake_sock.options
    finally:
        patcher.stop()
    return


def test_ttl_sets_ipv6_unicast_hops() -> None:
    """
        Verify ``ttl`` is forwarded to ``IPV6_UNICAST_HOPS`` for IPv6 sockets.
    """
    fake_sock, patcher = _establish_env()
    try:
        unicast.create_unicast_socket(
            "fe80::1", 5000, family=socket.AF_INET6, ttl=2
        )
        assert (IPPROTO_IPV6, socket.IPV6_UNICAST_HOPS, 2) in fake_sock.options
    finally:
        patcher.stop()
    return


def test_does_not_set_multicast_hops_or_loop() -> None:
    """
        Verify multicast-specific IPv6 options are not set on a unicast socket.
    """
    fake_sock, patcher = _establish_env()
    try:
        unicast.create_unicast_socket(
            "fe80::1", 5000, family=socket.AF_INET6, ttl=2
        )
        forbidden = {socket.IPV6_MULTICAST_HOPS, socket.IPV6_MULTICAST_LOOP}
        for _, optname, _ in fake_sock.options:
            assert optname not in forbidden
    finally:
        patcher.stop()
    return


def test_unsupported_family_raises_runtime_error() -> None:
    """
        Verify an unsupported address family raises ``RuntimeError``.
    """
    raised = False
    try:
        unicast.create_unicast_socket("192.168.1.1", 5000, family=99)
    except RuntimeError:
        raised = True
    assert raised
    return
