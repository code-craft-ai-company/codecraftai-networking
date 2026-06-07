"""
    .. module:: test_multicast
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Testbase tests for the :mod:`automojo.networking.multicast` module.

    .. moduleauthor:: Automojo Test Author
"""

import socket
import struct
from typing import List, Optional, Tuple
from unittest import mock

from automojo.networking import multicast
from automojo.networking.constants import IPPROTO_IPV6, SO_RECV_ANYIF


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


def _establish_socket_env() -> Tuple[FakeSocket, mock.MagicMock, mock._patch]:
    """
        Replicate the ``setUp`` used by the IPv4 and IPv6 listener tests by
        creating a :class:`FakeSocket` and patching ``socket.socket`` to return
        it.

        :returns: A tuple of the fake socket, the started socket mock, and the
                  patcher (so the caller can stop it during teardown).
    """
    fake_sock = FakeSocket()
    socket_patcher = mock.patch("socket.socket", return_value=fake_sock)
    mock_socket = socket_patcher.start()
    rtnval = (fake_sock, mock_socket, socket_patcher)
    return rtnval


def _establish_iface_socket_env() -> Tuple[
    FakeSocket, mock.MagicMock, mock._patch, mock._patch
]:
    """
        Replicate the ``setUp`` used by the per-interface listener tests by
        creating a :class:`FakeSocket`, patching ``socket.socket`` to return it,
        and patching ``socket.if_nametoindex`` to resolve to interface index 2.

        :returns: A tuple of the fake socket, the started socket mock, the
                  socket patcher, and the interface-index patcher (so the caller
                  can stop both during teardown).
    """
    fake_sock = FakeSocket()
    socket_patcher = mock.patch("socket.socket", return_value=fake_sock)
    mock_socket = socket_patcher.start()
    if_index_patcher = mock.patch("socket.if_nametoindex", return_value=2)
    if_index_patcher.start()
    rtnval = (fake_sock, mock_socket, socket_patcher, if_index_patcher)
    return rtnval


def test_creates_udp_socket_with_correct_family() -> None:
    """
        Verify the socket is created as AF_INET, SOCK_DGRAM, IPPROTO_UDP.
    """
    fake_sock, mock_socket, socket_patcher = _establish_socket_env()
    try:
        multicast.create_multicast_listener_socket(
            "224.0.0.1", 1900, family=socket.AF_INET
        )
        mock_socket.assert_called_with(
            socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP
        )
    finally:
        socket_patcher.stop()
    return


def test_full_option_set_for_ipv4_listener() -> None:
    """
        Verify all socket options and the bind address are configured for
        an IPv4 listener.
    """
    fake_sock, mock_socket, socket_patcher = _establish_socket_env()
    try:
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
        assert (socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) in fake_sock.options
        assert (
            socket.IPPROTO_IP,
            socket.IP_ADD_MEMBERSHIP,
            membership,
        ) in fake_sock.options
        assert (socket.SOL_SOCKET, SO_RECV_ANYIF, 1) in fake_sock.options
        assert (
            socket.IPPROTO_IP,
            socket.IP_MULTICAST_TTL,
            struct.pack("B", 2),
        ) in fake_sock.options
        assert (
            socket.IPPROTO_IP,
            socket.IP_MULTICAST_LOOP,
            struct.pack("b", 1),
        ) in fake_sock.options
        assert fake_sock.bound == ("1.2.3.4", 1900)
        assert fake_sock.timeout == 5
        assert rtnval is fake_sock
    finally:
        socket_patcher.stop()
    return


def test_no_ttl_option_when_ttl_omitted() -> None:
    """
        Verify the TTL option is not set when no TTL is supplied.
    """
    fake_sock, mock_socket, socket_patcher = _establish_socket_env()
    try:
        multicast.create_multicast_listener_socket(
            "224.0.0.1", 1900, bind_addr="0.0.0.0", family=socket.AF_INET
        )
        for _, optname, _ in fake_sock.options:
            assert optname != socket.IP_MULTICAST_TTL
    finally:
        socket_patcher.stop()
    return


def test_full_option_set_for_ipv6_listener() -> None:
    """
        Verify all socket options and the bind address are configured for
        an IPv6 listener.
    """
    fake_sock, mock_socket, socket_patcher = _establish_socket_env()
    try:
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
        assert (socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) in fake_sock.options
        assert (IPPROTO_IPV6, socket.IPV6_JOIN_GROUP, mreq) in fake_sock.options
        assert (socket.SOL_SOCKET, SO_RECV_ANYIF, 1) in fake_sock.options
        assert (IPPROTO_IPV6, socket.IPV6_MULTICAST_HOPS, 1) in fake_sock.options
        assert (IPPROTO_IPV6, socket.IPV6_MULTICAST_LOOP, 0) in fake_sock.options
        assert fake_sock.bound == ("::", 1900)
        assert fake_sock.timeout == 2
        assert rtnval is fake_sock
    finally:
        socket_patcher.stop()
    return


def test_unsupported_family_raises_runtime_error_error() -> None:
    """
        Verify an unsupported family raises ``RuntimeError``.
    """
    raised = False
    try:
        multicast.create_multicast_listener_socket(
            "224.0.0.1", 1900, family=99
        )
    except RuntimeError:
        raised = True
    assert raised
    return


def test_ipv4_iface_socket_sets_multicast_if_and_membership() -> None:
    """
        Verify the IPv4 per-interface listener sets ``IP_MULTICAST_IF`` and
        joins the multicast group with the interface IP.
    """
    fake_sock, mock_socket, socket_patcher, if_index_patcher = (
        _establish_iface_socket_env()
    )
    try:
        with mock.patch(
            "automojo.networking.multicast.get_ipv4_address",
            return_value="192.168.0.10",
        ):
            rtnval = multicast.create_multicast_listener_socket_for_iface(
                "eth0", "224.0.0.1", 1900, family=socket.AF_INET
            )

        mock_socket.assert_called_with(socket.AF_INET, socket.SOCK_DGRAM)
        iface_opt = (
            socket.IPPROTO_IP,
            socket.IP_MULTICAST_IF,
            socket.inet_aton("192.168.0.10"),
        )
        membership = (
            socket.inet_aton("224.0.0.1") + socket.inet_aton("192.168.0.10")
        )
        assert iface_opt in fake_sock.options
        assert (
            socket.IPPROTO_IP,
            socket.IP_ADD_MEMBERSHIP,
            membership,
        ) in fake_sock.options
        assert rtnval is fake_sock
    finally:
        socket_patcher.stop()
        if_index_patcher.stop()
    return


def test_ipv6_iface_socket_uses_interface_index() -> None:
    """
        Verify the IPv6 per-interface listener resolves the interface
        index and joins the IPv6 multicast group.
    """
    fake_sock, mock_socket, socket_patcher, if_index_patcher = (
        _establish_iface_socket_env()
    )
    try:
        with mock.patch(
            "automojo.networking.multicast.get_ipv6_address",
            return_value="fe80::1",
        ), mock.patch(
            "automojo.networking.multicast.socket.inet_aton",
            return_value=b"\x00" * 4,
        ):
            rtnval = multicast.create_multicast_listener_socket_for_iface(
                "eth0", "ff02::1", 1900, family=socket.AF_INET6
            )

        mock_socket.assert_called_with(socket.AF_INET6, socket.SOCK_DGRAM)
        mreq = socket.inet_pton(socket.AF_INET6, "ff02::1") + struct.pack("@I", 2)
        assert (IPPROTO_IPV6, socket.IPV6_JOIN_GROUP, mreq) in fake_sock.options
        assert rtnval is fake_sock
    finally:
        socket_patcher.stop()
        if_index_patcher.stop()
    return


def test_unsupported_family_raises_runtime_error_foriface() -> None:
    """
        Verify an unsupported family raises ``RuntimeError``.
    """
    fake_sock, mock_socket, socket_patcher, if_index_patcher = (
        _establish_iface_socket_env()
    )
    try:
        raised = False
        try:
            multicast.create_multicast_listener_socket_for_iface(
                "eth0", "224.0.0.1", 1900, family=99
            )
        except RuntimeError:
            raised = True
        assert raised
    finally:
        socket_patcher.stop()
        if_index_patcher.stop()
    return
