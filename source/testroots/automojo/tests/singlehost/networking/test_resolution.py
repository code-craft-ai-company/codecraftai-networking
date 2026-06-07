"""
    .. module:: test_resolution
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Testbase tests for the :mod:`automojo.networking.resolution`
                   module.

    .. moduleauthor:: Automojo Test Author
"""

from io import StringIO
from unittest import mock

import netifaces

from automojo.networking import resolution


def _establish_refresh_arp_env() -> dict:
    """
        Replicate the ``RefreshArpTableTests.setUp`` fixture by starting the
        ``os.system``, ``netifaces.ifaddresses`` and ``netifaces.interfaces``
        patchers and seeding the interface address return value.

        :returns: A dictionary carrying the started patchers and their mocks so
                  each test can use them and tear them down.
    """
    os_patcher = mock.patch("os.system")
    mock_os_system = os_patcher.start()
    ifaddrs_patcher = mock.patch("netifaces.ifaddresses")
    mock_ifaddresses = ifaddrs_patcher.start()
    interfaces_patcher = mock.patch(
        "netifaces.interfaces", return_value=["eth0", "lo"]
    )
    interfaces_patcher.start()

    mock_ifaddresses.return_value = {
        netifaces.AF_INET: [{"addr": "192.168.1.100"}]
    }

    env = {
        "os_patcher": os_patcher,
        "mock_os_system": mock_os_system,
        "ifaddrs_patcher": ifaddrs_patcher,
        "mock_ifaddresses": mock_ifaddresses,
        "interfaces_patcher": interfaces_patcher,
    }
    return env


def _teardown_refresh_arp_env(env: dict) -> None:
    """
        Replicate the ``RefreshArpTableTests.tearDown`` fixture by stopping the
        patchers started in :func:`_establish_refresh_arp_env`.

        :param env: The environment dictionary returned by
                    :func:`_establish_refresh_arp_env`.
    """
    env["os_patcher"].stop()
    env["ifaddrs_patcher"].stop()
    env["interfaces_patcher"].stop()
    return


def test_expand_with_leading_wildcard() -> None:
    """
        ``::1`` expands to a fully-qualified address.
    """
    rtnval = resolution.expand_ipv6_addr("::1")
    assert rtnval == "0:0:0:0:0:0:0:1"
    return


def test_expand_with_trailing_wildcard() -> None:
    """
        ``fe80::`` expands to a fully-qualified address.
    """
    rtnval = resolution.expand_ipv6_addr("fe80::")
    assert rtnval == "fe80:0:0:0:0:0:0:0"
    return


def test_expand_with_embedded_wildcard() -> None:
    """
        An address with an embedded ``::`` expands fully.
    """
    rtnval = resolution.expand_ipv6_addr("fe80::1")
    assert rtnval == "fe80:0:0:0:0:0:0:1"
    return


def test_expand_passthrough_for_already_expanded_address() -> None:
    """
        Already-expanded addresses are returned unchanged.
    """
    addr = "2001:0db8:85a3:0000:0000:8a2e:0370:7334"
    rtnval = resolution.expand_ipv6_addr(addr)
    assert rtnval == addr
    return


def test_invalid_double_wildcard_raises_value_error() -> None:
    """
        Multiple ``::`` sequences should raise ``ValueError``.
    """
    raised = False
    try:
        resolution.expand_ipv6_addr("fe80::1::2")
    except ValueError:
        raised = True
    assert raised
    return


def test_valid_addresses_return_true_ipv4() -> None:
    """
        Valid IPv4 strings produce ``True``.
    """
    assert resolution.is_ipv4_address("127.0.0.1")
    assert resolution.is_ipv4_address("255.255.255.255")
    assert resolution.is_ipv4_address("0.0.0.0")
    return


def test_out_of_range_components_return_false() -> None:
    """
        Components above 255 yield ``False``.
    """
    assert not resolution.is_ipv4_address("256.0.0.1")
    return


def test_non_numeric_components_return_false() -> None:
    """
        Non-numeric components yield ``False``.
    """
    assert not resolution.is_ipv4_address("abc.def.ghi.jkl")
    return


def test_wrong_component_count_returns_false() -> None:
    """
        Addresses with the wrong number of components yield ``False``.
    """
    assert not resolution.is_ipv4_address("1.2.3")
    assert not resolution.is_ipv4_address("1.2.3.4.5")
    return


def test_valid_addresses_return_true_ipv6() -> None:
    """
        Valid IPv6 strings produce ``True``.
    """
    assert resolution.is_ipv6_address("::1")
    assert resolution.is_ipv6_address("fe80::1")
    full_addr = "2001:0db8:85a3:0000:0000:8a2e:0370:7334"
    assert resolution.is_ipv6_address(full_addr)
    return


def test_invalid_hex_components_return_false() -> None:
    """
        Components containing non-hex characters yield ``False``.
    """
    assert not resolution.is_ipv6_address("gggg::1")
    return


def test_double_wildcard_raises_value_error() -> None:
    """
        Multiple ``::`` sequences must raise from the underlying expand call.
    """
    raised = False
    try:
        resolution.is_ipv6_address("fe80::1::2")
    except ValueError:
        raised = True
    assert raised
    return


def test_parses_proc_net_arp_table() -> None:
    """
        Verify a well-formed ``/proc/net/arp`` is parsed into a dictionary
        keyed by hardware address.
    """
    arp_data = (
        "IP address HW type Flags HW address Mask Device\n"
        "192.168.1.1 0x1 0x2 aa:bb:cc:dd:ee:ff * eth0\n"
        "10.0.0.1 0x1 0x2 11:22:33:44:55:66 * wlan0\n"
    )
    with mock.patch("builtins.open", return_value=StringIO(arp_data)):
        rtnval = resolution.get_arp_table()

    assert "aa:bb:cc:dd:ee:ff" in rtnval
    assert rtnval["aa:bb:cc:dd:ee:ff"]["ip"] == "192.168.1.1"
    assert rtnval["aa:bb:cc:dd:ee:ff"]["ifname"] == "eth0"
    assert "11:22:33:44:55:66" in rtnval
    return


def test_normalize_hwaddr_strips_colons_and_uppercases() -> None:
    """
        Verify the ``normalize_hwaddr`` flag yields uppercase, colon-free keys.
    """
    arp_data = (
        "IP address HW type Flags HW address Mask Device\n"
        "192.168.1.1 0x1 0x2 aa:bb:cc:dd:ee:ff * eth0\n"
    )
    with mock.patch("builtins.open", return_value=StringIO(arp_data)):
        rtnval = resolution.get_arp_table(normalize_hwaddr=True)

    assert "AABBCCDDEEFF" in rtnval
    assert rtnval["AABBCCDDEEFF"]["ip"] == "192.168.1.1"
    return


def test_returns_empty_dict_when_proc_net_arp_missing() -> None:
    """
        Verify a missing ``/proc/net/arp`` (non-Linux) returns ``{}``.
    """
    with mock.patch("builtins.open", side_effect=FileNotFoundError()):
        rtnval = resolution.get_arp_table()
    assert rtnval == {}
    return


def test_skips_lines_with_too_few_fields() -> None:
    """
        Verify malformed lines with fewer than 6 fields are skipped.
    """
    arp_data = (
        "IP address HW type Flags HW address Mask Device\n"
        "incomplete line\n"
        "192.168.1.1 0x1 0x2 aa:bb:cc:dd:ee:ff * eth0\n"
    )
    with mock.patch("builtins.open", return_value=StringIO(arp_data)):
        rtnval = resolution.get_arp_table()

    assert len(rtnval) == 1
    return


def test_invokes_ping_for_eligible_interfaces() -> None:
    """
        Verify a ping sweep is invoked for the prefix of each non-excluded
        interface IPv4 address.
    """
    env = _establish_refresh_arp_env()
    try:
        mock_os_system = env["mock_os_system"]
        resolution.refresh_arp_table()
        prefix = "192.168.1"
        expected_cmd = resolution.ARPING_RANGE_CMD % (prefix, prefix)
        mock_os_system.assert_called_with(expected_cmd)
    finally:
        _teardown_refresh_arp_env(env=env)
    return


def test_excludes_loopback_by_default() -> None:
    """
        Verify the default exclude list contains ``lo`` and prevents loopback
        from being scanned.
    """
    env = _establish_refresh_arp_env()
    try:
        mock_os_system = env["mock_os_system"]
        resolution.refresh_arp_table()
        for call_args in mock_os_system.call_args_list:
            cmd_str = call_args[0][0]
            assert "127.0" not in cmd_str
    finally:
        _teardown_refresh_arp_env(env=env)
    return


def test_include_interfaces_overrides_full_enumeration() -> None:
    """
        Verify supplying ``include_interfaces`` restricts the scan set.
    """
    env = _establish_refresh_arp_env()
    try:
        mock_os_system = env["mock_os_system"]
        resolution.refresh_arp_table(include_interfaces=["eth0"])
        assert mock_os_system.call_count >= 1
    finally:
        _teardown_refresh_arp_env(env=env)
    return


def test_returns_none() -> None:
    """
        Verify the function returns ``None``.
    """
    env = _establish_refresh_arp_env()
    try:
        rtnval = resolution.refresh_arp_table(include_interfaces=[])
        assert rtnval is None
    finally:
        _teardown_refresh_arp_env(env=env)
    return
