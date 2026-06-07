"""
    .. module:: test_broadcast
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Testbase tests for the :mod:`automojo.networking.broadcast` module.

    .. moduleauthor:: Automojo Test Author
"""

import socket
from typing import Optional, Tuple
from unittest import mock

from automojo.networking import broadcast


class FakeSocket:
    """
        Lightweight replacement for ``socket.socket`` capturing the parameters
        of a single ``sendto`` call.
    """

    def __init__(self) -> None:
        """
            Initialize a :class:`FakeSocket` instance.
        """
        self.sent_data: Optional[bytes] = None
        self.sent_addr: Optional[Tuple[str, int]] = None
        self.setsockopt_args: Optional[Tuple[int, int, int]] = None
        self.closed: bool = False
        return

    def setsockopt(self, level: int, optname: int, value: int) -> None:
        """
            Record the (level, optname, value) of a setsockopt call.
        """
        self.setsockopt_args = (level, optname, value)
        return

    def sendto(self, data: bytes, addr: Tuple[str, int]) -> None:
        """
            Record the data and destination address for a sendto call.
        """
        self.sent_data = data
        self.sent_addr = addr
        return

    def close(self) -> None:
        """
            Record the close call.
        """
        self.closed = True
        return


def _establish_env() -> Tuple[FakeSocket, "mock._patch"]:
    """
        Replicate the original ``setUp`` for the broadcast wake-on-lan tests by
        creating a :class:`FakeSocket` and starting a patch that replaces
        ``socket.socket`` with that fake.

        :returns: A tuple of the :class:`FakeSocket` instance and the started
                  patcher, the latter so callers can stop it during teardown.
    """
    fake_sock = FakeSocket()
    patcher = mock.patch("socket.socket", return_value=fake_sock)
    patcher.start()
    rtnval = (fake_sock, patcher)
    return rtnval


def test_invalid_mac_raises_value_error() -> None:
    """
        Verify a malformed MAC raises ``ValueError``.
    """
    fake_sock, patcher = _establish_env()
    try:
        raised = False
        try:
            broadcast.broadcast_wake_on_lan_magic_message(
                "255.255.255.255", "00:00:00:00:00"
            )
        except ValueError:
            raised = True
        assert raised
    finally:
        patcher.stop()
    return


def test_packet_destination_is_broadcast_port_9() -> None:
    """
        Verify the magic packet is sent to the broadcast address on UDP port 9.
    """
    fake_sock, patcher = _establish_env()
    try:
        broadcast.broadcast_wake_on_lan_magic_message(
            "255.255.255.255", "AA:BB:CC:DD:EE:FF"
        )
        assert fake_sock.sent_addr == ("255.255.255.255", 9)
    finally:
        patcher.stop()
    return


def test_packet_length_is_102_bytes() -> None:
    """
        Verify the magic packet is 102 bytes (6 sync + 16 * 6 mac).
    """
    fake_sock, patcher = _establish_env()
    try:
        broadcast.broadcast_wake_on_lan_magic_message(
            "255.255.255.255", "AA:BB:CC:DD:EE:FF"
        )
        assert len(fake_sock.sent_data) == 102
    finally:
        patcher.stop()
    return


def test_packet_starts_with_six_ff_bytes() -> None:
    """
        Verify the packet begins with the six-byte FF synchronization stream.
    """
    fake_sock, patcher = _establish_env()
    try:
        broadcast.broadcast_wake_on_lan_magic_message(
            "255.255.255.255", "AA:BB:CC:DD:EE:FF"
        )
        prefix = fake_sock.sent_data[:6]
        assert prefix == b"\xff" * 6
    finally:
        patcher.stop()
    return


def test_packet_repeats_mac_sixteen_times() -> None:
    """
        Verify the MAC address payload appears 16 times after the sync header.
    """
    fake_sock, patcher = _establish_env()
    try:
        broadcast.broadcast_wake_on_lan_magic_message(
            "255.255.255.255", "AA:BB:CC:DD:EE:FF"
        )
        mac_bytes = bytes.fromhex("AABBCCDDEEFF")
        payload = fake_sock.sent_data[6:]
        for idx in range(16):
            chunk = payload[idx * 6:(idx + 1) * 6]
            assert chunk == mac_bytes
    finally:
        patcher.stop()
    return


def test_dash_delimited_mac_supported() -> None:
    """
        Verify dash-delimited MAC addresses are also accepted.
    """
    fake_sock, patcher = _establish_env()
    try:
        broadcast.broadcast_wake_on_lan_magic_message(
            "255.255.255.255", "AA-BB-CC-DD-EE-FF"
        )
        assert len(fake_sock.sent_data) == 102
    finally:
        patcher.stop()
    return


def test_so_broadcast_set() -> None:
    """
        Verify the broadcast socket option is enabled.
    """
    fake_sock, patcher = _establish_env()
    try:
        broadcast.broadcast_wake_on_lan_magic_message(
            "255.255.255.255", "AA:BB:CC:DD:EE:FF"
        )
        assert fake_sock.setsockopt_args == (
            socket.SOL_SOCKET,
            socket.SO_BROADCAST,
            1,
        )
    finally:
        patcher.stop()
    return


def test_socket_closed_on_success() -> None:
    """
        Verify the socket is closed after a successful send.
    """
    fake_sock, patcher = _establish_env()
    try:
        broadcast.broadcast_wake_on_lan_magic_message(
            "255.255.255.255", "AA:BB:CC:DD:EE:FF"
        )
        assert fake_sock.closed
    finally:
        patcher.stop()
    return
