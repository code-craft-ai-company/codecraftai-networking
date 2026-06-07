"""
    .. module:: test_arp
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Testbase tests for the :mod:`automojo.networking.arp` module.

    .. moduleauthor:: Automojo Test Author
"""

import subprocess
from unittest import mock

from automojo.networking import arp


def test_parses_populated_linux_output() -> None:
    """
        Verify the parser produces standardized entries from ``ip neigh`` output.
    """
    linux_output = (
        "192.168.1.1 dev eth0 lladdr 00:1d:a1:b1:c5:df REACHABLE\n"
        "10.0.0.1 dev wlan0 lladdr 5c:bd:e2:2e:a3:25 STALE\n"
    )
    with mock.patch("platform.system", return_value="Linux"), mock.patch(
        "subprocess.check_output", return_value=linux_output
    ):
        rtnval = arp.get_arp_table()

    expected = [
        {
            "IPAddress": "192.168.1.1",
            "HWType": "eth0",
            "MACAddress": "00:1d:a1:b1:c5:df",
        },
        {
            "IPAddress": "10.0.0.1",
            "HWType": "wlan0",
            "MACAddress": "5c:bd:e2:2e:a3:25",
        },
    ]
    assert rtnval == expected
    return


def test_returns_empty_list_for_empty_output_linux() -> None:
    """
        Verify an empty ARP table yields an empty result list.
    """
    with mock.patch("platform.system", return_value="Linux"), mock.patch(
        "subprocess.check_output", return_value=""
    ):
        rtnval = arp.get_arp_table()
    assert rtnval == []
    return


def test_skips_incomplete_entries_without_lladdr() -> None:
    """
        Verify lines lacking a hardware address (incomplete entries) are skipped.
    """
    linux_output = (
        "192.168.1.50 dev eth0  FAILED\n"
        "192.168.1.1 dev eth0 lladdr 00:1d:a1:b1:c5:df REACHABLE\n"
    )
    with mock.patch("platform.system", return_value="Linux"), mock.patch(
        "subprocess.check_output", return_value=linux_output
    ):
        rtnval = arp.get_arp_table()
    assert len(rtnval) == 1
    assert rtnval[0]["IPAddress"] == "192.168.1.1"
    return


def test_handles_ipv6_neighbor_entries() -> None:
    """
        Verify IPv6 neighbour entries are parsed.
    """
    linux_output = "fe80::1 dev eth0 lladdr aa:bb:cc:dd:ee:ff router REACHABLE\n"
    with mock.patch("platform.system", return_value="Linux"), mock.patch(
        "subprocess.check_output", return_value=linux_output
    ):
        rtnval = arp.get_arp_table()
    assert len(rtnval) == 1
    assert rtnval[0]["IPAddress"] == "fe80::1"
    assert rtnval[0]["MACAddress"] == "aa:bb:cc:dd:ee:ff"
    return


def test_parses_populated_windows_output() -> None:
    """
        Verify the parser produces standardized entries from ``arp -a`` output.
    """
    windows_output = (
        "Interface: 192.168.1.2 --- 0x3\n"
        "  Internet Address      Physical Address      Type\n"
        "  192.168.1.1           00-1D-A1-B1-C5-DF     dynamic\n"
        "  10.0.0.1              5c-bd-e2-2e-a3-25     dynamic\n"
    )
    with mock.patch("platform.system", return_value="Windows"), mock.patch(
        "subprocess.check_output", return_value=windows_output
    ):
        rtnval = arp.get_arp_table()

    expected = [
        {
            "IPAddress": "192.168.1.1",
            "HWType": "dynamic",
            "MACAddress": "00-1D-A1-B1-C5-DF",
        },
        {
            "IPAddress": "10.0.0.1",
            "HWType": "dynamic",
            "MACAddress": "5c-bd-e2-2e-a3-25",
        },
    ]
    assert rtnval == expected
    return


def test_returns_empty_list_for_empty_output_windows() -> None:
    """
        Verify an empty Windows ARP table yields an empty result list.
    """
    with mock.patch("platform.system", return_value="Windows"), mock.patch(
        "subprocess.check_output", return_value=""
    ):
        rtnval = arp.get_arp_table()
    assert rtnval == []
    return


def test_returns_empty_list_when_subprocess_fails() -> None:
    """
        Verify a CalledProcessError causes the function to return ``[]``
        and swallow the failure.
    """
    err = subprocess.CalledProcessError(returncode=1, cmd=["ip", "neigh"])
    with mock.patch("platform.system", return_value="Linux"), mock.patch(
        "subprocess.check_output", side_effect=err
    ):
        rtnval = arp.get_arp_table()
    assert rtnval == []
    return
