"""
    .. module:: broadcast
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Module that contains broadcast helper functions.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


def broadcast_wake_on_lan_magic_message(brodcast_addr: str, mac_addr: str):
    """
        Broadcasts a Wake-on-LAN magic message.

        :param brodcast_addr: The broadcast address to send the magic packet to.
        :param mac_addr: The MAC address of the device to wake.

        :returns: ``None``
    """
    import socket

    mac_bytes = mac_addr.replace(":", "").replace("-", "")
    if len(mac_bytes) != 12:
        raise ValueError(f"Invalid MAC address: {mac_addr}")

    magic_packet = bytes.fromhex("FF" * 6 + mac_bytes * 16)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.sendto(magic_packet, (brodcast_addr, 9))
    finally:
        sock.close()

    return
