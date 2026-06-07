"""
    .. module:: test_interface_class_vpn_overlay
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Unit tests for the VPN_OVERLAY extension to
                   :class:`automojo.networking.interfaces.InterfaceClass`,
                   :class:`InterfaceDescriptor`, and
                   :func:`detect_overlay_provider`.

    .. moduleauthor:: Automojo Test Author
"""

from automojo.errors.exceptions import ConfigurationError
from automojo.networking.interfaces import (
    InterfaceClass,
    InterfaceDescriptor,
    detect_overlay_provider,
)


def test_vpn_overlay_member_present_with_value_6() -> None:
    """
        Verify ``VPN_OVERLAY`` exists with integer value ``6``.
    """
    assert int(InterfaceClass.VPN_OVERLAY) == 6
    return


def test_existing_members_unchanged() -> None:
    """
        Verify pre-existing members retain their integer values for
        serialisation compatibility.
    """
    assert int(InterfaceClass.UNKNOWN) == 0
    assert int(InterfaceClass.LOOPBACK) == 1
    assert int(InterfaceClass.BRIDGE) == 2
    assert int(InterfaceClass.WIRED) == 3
    assert int(InterfaceClass.WIRELESS) == 4
    assert int(InterfaceClass.TUNNEL) == 5
    return


def test_interface_class_serialisation_round_trip() -> None:
    """
        Verify ``InterfaceClass(6)`` and ``InterfaceClass["VPN_OVERLAY"]``
        both yield the ``VPN_OVERLAY`` member.
    """
    from_int = InterfaceClass(6)
    from_name = InterfaceClass["VPN_OVERLAY"]
    assert from_int is InterfaceClass.VPN_OVERLAY
    assert from_name is InterfaceClass.VPN_OVERLAY
    return


def test_descriptor_wired_no_provider_ok() -> None:
    """
        Verify a wired descriptor without a provider constructs.
    """
    d = InterfaceDescriptor(name="eth0", interface_class=InterfaceClass.WIRED)
    assert d.name == "eth0"
    assert d.provider is None
    return


def test_descriptor_overlay_with_provider_ok() -> None:
    """
        Verify an overlay descriptor with a valid provider constructs.
    """
    d = InterfaceDescriptor(
        name="tailscale0",
        interface_class=InterfaceClass.VPN_OVERLAY,
        provider="tailscale",
    )
    assert d.provider == "tailscale"
    return


def test_descriptor_overlay_without_provider_raises() -> None:
    """
        Verify ``VPN_OVERLAY`` without a provider raises.
    """
    raised = False
    try:
        InterfaceDescriptor(
            name="tailscale0",
            interface_class=InterfaceClass.VPN_OVERLAY,
            provider=None,
        )
    except ConfigurationError:
        raised = True

    assert raised
    return


def test_descriptor_non_overlay_with_provider_raises() -> None:
    """
        Verify a non-overlay class with a provider raises.
    """
    raised = False
    try:
        InterfaceDescriptor(
            name="eth0",
            interface_class=InterfaceClass.WIRED,
            provider="tailscale",
        )
    except ConfigurationError:
        raised = True

    assert raised
    return


def test_descriptor_overlay_unsupported_provider_raises() -> None:
    """
        Verify an unsupported provider value raises.
    """
    raised = False
    try:
        InterfaceDescriptor(
            name="tailscale0",
            interface_class=InterfaceClass.VPN_OVERLAY,
            provider="nordvpn",
        )
    except ConfigurationError:
        raised = True

    assert raised
    return


def test_detect_overlay_provider_table() -> None:
    """
        Verify well-known patterns map to the expected provider id.
    """
    cases = [
        ("tailscale0", "tailscale"),
        ("utun3", "tailscale"),
        ("sdwan0", "twingate"),
        ("twingate1", "twingate"),
        ("eth0", None),
    ]
    for ifname, expected in cases:
        actual = detect_overlay_provider(name=ifname)
        assert actual == expected, f"ifname={ifname!r}"
    return
