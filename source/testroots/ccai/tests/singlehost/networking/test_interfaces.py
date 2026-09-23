"""
    .. module:: test_interfaces
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Testbase tests for the :mod:`ccai.networking.interfaces` module.

    .. moduleauthor:: CodeCraftAI Test Author
"""

import socket
from typing import Dict, Tuple
from unittest import mock

import netifaces

from ccai.networking import interfaces
from ccai.networking.interfaces import InterfaceClass


def _establish_ipv4_env() -> Tuple[Dict[str, dict], "mock._patch", "mock._patch"]:
    """
        Replicate the original ``GetAllIpv4InterfacesTests.setUp`` by starting
        patches for ``netifaces.interfaces`` and ``netifaces.ifaddresses`` that
        serve a fixed interface name list and a mutable address map.

        :returns: A tuple of the mutable address map and the two started
                  patchers, the latter so callers can stop them during teardown.
    """
    ifnames = ["eth0", "lo", "wlan0"]
    interfaces_patcher = mock.patch("netifaces.interfaces", return_value=ifnames)
    interfaces_patcher.start()

    addr_map = {
        "eth0": {netifaces.AF_INET: [{"addr": "192.168.1.10"}]},
        "lo": {netifaces.AF_INET: [{"addr": "127.0.0.1"}]},
        "wlan0": {netifaces.AF_INET6: [{"addr": "fe80::1"}]},
    }

    def fake_ifaddresses(ifname: str) -> dict:
        rtnval = addr_map.get(ifname, {})
        return rtnval

    ifaddresses_patcher = mock.patch(
        "netifaces.ifaddresses", side_effect=fake_ifaddresses
    )
    ifaddresses_patcher.start()

    rtnval = (addr_map, interfaces_patcher, ifaddresses_patcher)
    return rtnval


def _establish_ipv6_env() -> Tuple[Dict[str, dict], "mock._patch", "mock._patch"]:
    """
        Replicate the original ``GetAllIpv6InterfacesTests.setUp`` by starting
        patches for ``netifaces.interfaces`` and ``netifaces.ifaddresses`` that
        serve a fixed interface name list and a mutable address map.

        :returns: A tuple of the mutable address map and the two started
                  patchers, the latter so callers can stop them during teardown.
    """
    ifnames = ["eth0", "lo", "wlan0"]
    interfaces_patcher = mock.patch("netifaces.interfaces", return_value=ifnames)
    interfaces_patcher.start()

    addr_map = {
        "eth0": {
            netifaces.AF_INET: [{"addr": "192.168.1.10"}],
            netifaces.AF_INET6: [{"addr": "fe80::1"}],
        },
        "lo": {netifaces.AF_INET: [{"addr": "127.0.0.1"}]},
        "wlan0": {netifaces.AF_INET6: [{"addr": "fe80::2"}]},
    }

    def fake_ifaddresses(ifname: str) -> dict:
        rtnval = addr_map.get(ifname, {})
        return rtnval

    ifaddresses_patcher = mock.patch(
        "netifaces.ifaddresses", side_effect=fake_ifaddresses
    )
    ifaddresses_patcher.start()

    rtnval = (addr_map, interfaces_patcher, ifaddresses_patcher)
    return rtnval


def test_encode_ipv4_address_returns_four_bytes() -> None:
    """
        Encoding an IPv4 address should produce a 4-byte packed value.
    """
    rtnval = interfaces.encode_address("192.168.1.1")
    assert len(rtnval) == 4
    assert rtnval == socket.inet_pton(socket.AF_INET, "192.168.1.1")
    return


def test_encode_ipv6_address_returns_sixteen_bytes() -> None:
    """
        Encoding an IPv6 address should produce a 16-byte packed value.
    """
    rtnval = interfaces.encode_address("fe80::1")
    assert len(rtnval) == 16
    assert rtnval == socket.inet_pton(socket.AF_INET6, "fe80::1")
    return


def test_returns_only_ipv4_interfaces() -> None:
    """
        Verify only interfaces with IPv4 addresses are returned.
    """
    addr_map, interfaces_patcher, ifaddresses_patcher = _establish_ipv4_env()
    try:
        rtnval = interfaces.get_all_ipv4_interfaces()
        expected = ["eth0", "lo"]
        assert rtnval == expected
    finally:
        interfaces_patcher.stop()
        ifaddresses_patcher.stop()
    return


def test_returns_empty_list_when_no_ipv4() -> None:
    """
        Verify an empty list is returned when no IPv4-capable interfaces exist.
    """
    addr_map, interfaces_patcher, ifaddresses_patcher = _establish_ipv4_env()
    try:
        addr_map.clear()
        rtnval = interfaces.get_all_ipv4_interfaces()
        assert rtnval == []
    finally:
        interfaces_patcher.stop()
        ifaddresses_patcher.stop()
    return


def test_skips_interfaces_with_empty_ipv4_list() -> None:
    """
        An interface with an empty AF_INET list should be skipped.
    """
    addr_map, interfaces_patcher, ifaddresses_patcher = _establish_ipv4_env()
    try:
        addr_map["eth0"] = {netifaces.AF_INET: []}
        rtnval = interfaces.get_all_ipv4_interfaces()
        assert "eth0" not in rtnval
    finally:
        interfaces_patcher.stop()
        ifaddresses_patcher.stop()
    return


def test_returns_only_ipv6_interfaces() -> None:
    """
        Verify only interfaces with IPv6 addresses are returned.
    """
    addr_map, interfaces_patcher, ifaddresses_patcher = _establish_ipv6_env()
    try:
        rtnval = interfaces.get_all_ipv6_interfaces()
        expected = ["eth0", "wlan0"]
        assert rtnval == expected
    finally:
        interfaces_patcher.stop()
        ifaddresses_patcher.stop()
    return


def test_returns_empty_list_when_no_ipv6() -> None:
    """
        Verify an empty list is returned when no IPv6-capable interfaces exist.
    """
    addr_map, interfaces_patcher, ifaddresses_patcher = _establish_ipv6_env()
    try:
        addr_map["eth0"] = {netifaces.AF_INET: [{"addr": "192.168.1.10"}]}
        del addr_map["wlan0"]
        rtnval = interfaces.get_all_ipv6_interfaces()
        assert rtnval == []
    finally:
        interfaces_patcher.stop()
        ifaddresses_patcher.stop()
    return


def test_returns_ipv4_address_when_available() -> None:
    """
        Verify the first IPv4 address is returned for an interface.
    """
    addr_table = {netifaces.AF_INET: [{"addr": "10.0.0.5"}]}
    with mock.patch("netifaces.ifaddresses", return_value=addr_table):
        rtnval = interfaces.get_ipv4_address("eth0")
    assert rtnval == "10.0.0.5"
    return


def test_returns_none_when_no_ipv4() -> None:
    """
        Verify ``None`` is returned when the interface has no IPv4 address.
    """
    addr_table = {netifaces.AF_INET6: [{"addr": "fe80::1"}]}
    with mock.patch("netifaces.ifaddresses", return_value=addr_table):
        rtnval = interfaces.get_ipv4_address("eth0")
    assert rtnval is None
    return


def test_returns_ipv6_address_when_available() -> None:
    """
        Verify the first IPv6 address is returned for an interface.
    """
    addr_table = {
        netifaces.AF_INET6: [{"addr": "fe80::1"}],
        netifaces.AF_INET: [{"addr": "127.0.0.1"}],
    }
    with mock.patch("netifaces.ifaddresses", return_value=addr_table):
        rtnval = interfaces.get_ipv6_address("eth0")
    assert rtnval == "fe80::1"
    return


def test_returns_none_when_no_ipv6() -> None:
    """
        Verify ``None`` is returned when the interface has no IPv6 address.
    """
    addr_table = {netifaces.AF_INET: [{"addr": "10.0.0.5"}]}
    with mock.patch("netifaces.ifaddresses", return_value=addr_table):
        rtnval = interfaces.get_ipv6_address("eth0")
    assert rtnval is None
    return


def test_returns_local_socket_address_on_success() -> None:
    """
        Verify the function returns the local socket name's address
        after connecting.
    """
    mock_sock = mock.MagicMock()
    mock_sock.getsockname.return_value = ("10.0.0.5", 12345)

    with mock.patch("socket.socket", return_value=mock_sock):
        rtnval = interfaces.get_correspondance_ip_address("8.8.8.8", ref_port=53)

    assert rtnval == "10.0.0.5"
    mock_sock.connect.assert_called_once_with(("8.8.8.8", 53))
    mock_sock.close.assert_called_once()
    return


def test_returns_none_on_connect_failure() -> None:
    """
        Verify the function returns ``None`` when connect raises.
    """
    mock_sock = mock.MagicMock()
    mock_sock.connect.side_effect = OSError("Network unreachable")

    with mock.patch("socket.socket", return_value=mock_sock):
        rtnval = interfaces.get_correspondance_ip_address("8.8.8.8", ref_port=53)

    assert rtnval is None
    mock_sock.close.assert_called_once()
    return


def test_returns_none_when_no_correspondance_ip() -> None:
    """
        Verify both returns are ``None`` when no correspondence IP is found.
    """
    with mock.patch(
        "ccai.networking.interfaces.get_correspondance_ip_address",
        return_value=None,
    ) as gcia, mock.patch(
        "ccai.networking.interfaces.get_interface_for_ip"
    ) as gifip:
        iface, ip = interfaces.get_correspondance_interface("1.1.1.1", 80)
        gcia.assert_called_once()
        gifip.assert_not_called()

    assert ip is None
    assert iface is None
    return


def test_returns_tuple_when_ip_resolved() -> None:
    """
        Verify the (interface, ip) tuple is returned on success.
    """
    with mock.patch(
        "ccai.networking.interfaces.get_correspondance_ip_address",
        return_value="1.2.3.4",
    ), mock.patch(
        "ccai.networking.interfaces.get_interface_for_ip",
        return_value="eth0",
    ):
        iface, ip = interfaces.get_correspondance_interface("1.1.1.1", 80)

    assert ip == "1.2.3.4"
    assert iface == "eth0"
    return


def test_returns_matching_interface_name() -> None:
    """
        Verify the interface name owning the address is returned.
    """
    addr_info = [(socket.AF_INET, None, None, None, None)]
    ifnames = ["lo", "eth0"]
    addr_map = {
        "lo": {netifaces.AF_INET: [{"addr": "127.0.0.1"}]},
        "eth0": {netifaces.AF_INET: [{"addr": "10.0.0.5"}]},
    }

    def fake_ifaddresses(ifname: str) -> dict:
        rtnval = addr_map.get(ifname, {})
        return rtnval

    with mock.patch("socket.getaddrinfo", return_value=addr_info), mock.patch(
        "netifaces.interfaces", return_value=ifnames
    ), mock.patch("netifaces.ifaddresses", side_effect=fake_ifaddresses):
        rtnval = interfaces.get_interface_for_ip("10.0.0.5")

    assert rtnval == "eth0"
    return


def test_returns_none_when_no_match() -> None:
    """
        Verify ``None`` is returned when no interface owns the address.
    """
    addr_info = [(socket.AF_INET, None, None, None, None)]
    ifnames = ["lo"]
    addr_map = {
        "lo": {netifaces.AF_INET: [{"addr": "127.0.0.1"}]},
    }

    def fake_ifaddresses(ifname: str) -> dict:
        rtnval = addr_map.get(ifname, {})
        return rtnval

    with mock.patch("socket.getaddrinfo", return_value=addr_info), mock.patch(
        "netifaces.interfaces", return_value=ifnames
    ), mock.patch("netifaces.ifaddresses", side_effect=fake_ifaddresses):
        rtnval = interfaces.get_interface_for_ip("10.0.0.5")

    assert rtnval is None
    return


def test_raises_filenotfound_when_syspath_missing() -> None:
    """
        Verify a missing /sys/class/net path raises FileNotFoundError.
    """
    with mock.patch("os.path.exists", return_value=False):
        raised = False
        try:
            interfaces.get_interface_class("eth0")
        except FileNotFoundError:
            raised = True
        assert raised
    return


def test_returns_wireless_when_wireless_dir_present() -> None:
    """
        Verify a directory listing containing 'wireless' yields WIRELESS.
    """
    with mock.patch("os.path.exists", return_value=True), mock.patch(
        "os.listdir", return_value=["wireless", "address"]
    ):
        rtnval = interfaces.get_interface_class("wlan0")
    assert rtnval == InterfaceClass.WIRELESS
    return


def test_returns_bridge_when_bridge_dir_present() -> None:
    """
        Verify a directory listing containing 'bridge' yields BRIDGE.
    """
    with mock.patch("os.path.exists", return_value=True), mock.patch(
        "os.listdir", return_value=["bridge", "address"]
    ):
        rtnval = interfaces.get_interface_class("br0")
    assert rtnval == InterfaceClass.BRIDGE
    return


def test_returns_loopback_when_flags_indicate() -> None:
    """
        Verify ifconfig flags containing 'LOOPBACK' yield LOOPBACK.
    """
    ifconfig_output = "lo: flags=8049<UP,LOOPBACK,RUNNING,MULTICAST>\n"
    with mock.patch("os.path.exists", return_value=True), mock.patch(
        "os.listdir", return_value=["address"]
    ), mock.patch(
        "subprocess.check_output", return_value=ifconfig_output.encode("utf8")
    ):
        rtnval = interfaces.get_interface_class("lo")
    assert rtnval == InterfaceClass.LOOPBACK
    return


def test_returns_tunnel_when_flags_indicate_p2p() -> None:
    """
        Verify ifconfig flags containing 'POINTTOPOINT' yield TUNNEL.
    """
    ifconfig_output = "tun0: flags=8051<UP,POINTTOPOINT,RUNNING>\n"
    with mock.patch("os.path.exists", return_value=True), mock.patch(
        "os.listdir", return_value=["address"]
    ), mock.patch(
        "subprocess.check_output", return_value=ifconfig_output.encode("utf8")
    ):
        rtnval = interfaces.get_interface_class("tun0")
    assert rtnval == InterfaceClass.TUNNEL
    return


def test_returns_wired_when_no_special_flags() -> None:
    """
        Verify a regular interface yields WIRED.
    """
    ifconfig_output = "eth0: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>\n"
    with mock.patch("os.path.exists", return_value=True), mock.patch(
        "os.listdir", return_value=["address"]
    ), mock.patch(
        "subprocess.check_output", return_value=ifconfig_output.encode("utf8")
    ):
        rtnval = interfaces.get_interface_class("eth0")
    assert rtnval == InterfaceClass.WIRED
    return


def test_table_aggregates_classes_for_each_interface() -> None:
    """
        Verify the table maps every interface name to a class.
    """
    ifnames = ["lo", "eth0"]

    def fake_get_class(ifname: str) -> InterfaceClass:
        rtnval = (
            InterfaceClass.LOOPBACK
            if ifname == "lo"
            else InterfaceClass.WIRED
        )
        return rtnval

    with mock.patch("netifaces.interfaces", return_value=ifnames), mock.patch(
        "ccai.networking.interfaces.get_interface_class",
        side_effect=fake_get_class,
    ):
        rtnval = interfaces.get_interface_class_table()

    expected = {"lo": InterfaceClass.LOOPBACK, "eth0": InterfaceClass.WIRED}
    assert rtnval == expected
    return


def test_filter_returns_only_matching_class() -> None:
    """
        Verify the filter helper returns only interfaces of the given class.
    """
    table = {
        "lo": InterfaceClass.LOOPBACK,
        "eth0": InterfaceClass.WIRED,
        "wlan0": InterfaceClass.WIRELESS,
    }
    with mock.patch(
        "ccai.networking.interfaces.get_interface_class_table",
        return_value=table,
    ):
        rtnval = interfaces.get_interface_names_of_class(InterfaceClass.WIRELESS)
    assert rtnval == ["wlan0"]
    return


def test_returns_true_for_16_byte_input() -> None:
    """
        Verify a 16-byte raw input is treated as IPv6.
    """
    rtnval = interfaces.is_ipv6_address("0123456789abcdef")
    assert rtnval
    return


def test_returns_false_for_other_lengths() -> None:
    """
        Verify non-16-byte input is rejected.
    """
    rtnval = interfaces.is_ipv6_address("1234")
    assert not rtnval
    return
