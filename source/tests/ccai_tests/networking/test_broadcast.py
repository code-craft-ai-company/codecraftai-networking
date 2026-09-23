"""
    .. module:: test_broadcast
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Unit tests for the :mod:`ccai.networking.broadcast` module.

    .. moduleauthor:: CodeCraftAI Test Author
"""

import socket
import unittest
from typing import Optional, Tuple
import unittest.mock

from ccai.networking import broadcast


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


class BroadcastWakeOnLanTests(unittest.TestCase):
    """
        Tests for :func:`broadcast.broadcast_wake_on_lan_magic_message`.
    """

    def setUp(self) -> None:
        self.fake_sock = FakeSocket()
        self.patcher = unittest.mock.patch("socket.socket", return_value=self.fake_sock)
        self.patcher.start()
        return

    def tearDown(self) -> None:
        self.patcher.stop()
        return

    def test_invalid_mac_raises_value_error(self) -> None:
        """
            Verify a malformed MAC raises ``ValueError``.
        """
        with self.assertRaises(ValueError):
            broadcast.broadcast_wake_on_lan_magic_message(
                "255.255.255.255", "00:00:00:00:00"
            )
        return

    def test_packet_destination_is_broadcast_port_9(self) -> None:
        """
            Verify the magic packet is sent to the broadcast address on UDP port 9.
        """
        broadcast.broadcast_wake_on_lan_magic_message(
            "255.255.255.255", "AA:BB:CC:DD:EE:FF"
        )
        self.assertEqual(self.fake_sock.sent_addr, ("255.255.255.255", 9))
        return

    def test_packet_length_is_102_bytes(self) -> None:
        """
            Verify the magic packet is 102 bytes (6 sync + 16 * 6 mac).
        """
        broadcast.broadcast_wake_on_lan_magic_message(
            "255.255.255.255", "AA:BB:CC:DD:EE:FF"
        )
        self.assertEqual(len(self.fake_sock.sent_data), 102)
        return

    def test_packet_starts_with_six_ff_bytes(self) -> None:
        """
            Verify the packet begins with the six-byte FF synchronization stream.
        """
        broadcast.broadcast_wake_on_lan_magic_message(
            "255.255.255.255", "AA:BB:CC:DD:EE:FF"
        )
        prefix = self.fake_sock.sent_data[:6]
        self.assertEqual(prefix, b"\xff" * 6)
        return

    def test_packet_repeats_mac_sixteen_times(self) -> None:
        """
            Verify the MAC address payload appears 16 times after the sync header.
        """
        broadcast.broadcast_wake_on_lan_magic_message(
            "255.255.255.255", "AA:BB:CC:DD:EE:FF"
        )
        mac_bytes = bytes.fromhex("AABBCCDDEEFF")
        payload = self.fake_sock.sent_data[6:]
        for idx in range(16):
            chunk = payload[idx * 6:(idx + 1) * 6]
            self.assertEqual(chunk, mac_bytes)
        return

    def test_dash_delimited_mac_supported(self) -> None:
        """
            Verify dash-delimited MAC addresses are also accepted.
        """
        broadcast.broadcast_wake_on_lan_magic_message(
            "255.255.255.255", "AA-BB-CC-DD-EE-FF"
        )
        self.assertEqual(len(self.fake_sock.sent_data), 102)
        return

    def test_so_broadcast_set(self) -> None:
        """
            Verify the broadcast socket option is enabled.
        """
        broadcast.broadcast_wake_on_lan_magic_message(
            "255.255.255.255", "AA:BB:CC:DD:EE:FF"
        )
        self.assertEqual(
            self.fake_sock.setsockopt_args,
            (socket.SOL_SOCKET, socket.SO_BROADCAST, 1),
        )
        return

    def test_socket_closed_on_success(self) -> None:
        """
            Verify the socket is closed after a successful send.
        """
        broadcast.broadcast_wake_on_lan_magic_message(
            "255.255.255.255", "AA:BB:CC:DD:EE:FF"
        )
        self.assertTrue(self.fake_sock.closed)
        return


if __name__ == "__main__":
    unittest.main()
