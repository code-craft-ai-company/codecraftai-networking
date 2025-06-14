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
        [FF FF FF FF FF FF] + [mac] * 16   ( len 102 bytes )
    """
    return
