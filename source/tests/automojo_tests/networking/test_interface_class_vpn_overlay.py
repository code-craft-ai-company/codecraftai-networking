"""
    .. module:: test_interface_class_vpn_overlay
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Unit tests for the VPN_OVERLAY extension to
                   :class:`automojo.networking.interfaces.InterfaceClass`,
                   :class:`InterfaceDescriptor`, and
                   :func:`detect_overlay_provider`.

    .. moduleauthor:: Automojo Test Author
"""

import unittest

from automojo.errors.exceptions import ConfigurationError
from automojo.networking.interfaces import (
    InterfaceClass,
    InterfaceDescriptor,
    detect_overlay_provider,
)


class InterfaceClassMemberTests(unittest.TestCase):
    """
        Enum-member presence and stability tests.
    """

    def test_vpn_overlay_member_present_with_value_6(self) -> None:
        """
            Verify ``VPN_OVERLAY`` exists with integer value ``6``.
        """
        self.assertEqual(int(InterfaceClass.VPN_OVERLAY), 6)
        return

    def test_existing_members_unchanged(self) -> None:
        """
            Verify pre-existing members retain their integer values for
            serialisation compatibility.
        """
        self.assertEqual(int(InterfaceClass.UNKNOWN), 0)
        self.assertEqual(int(InterfaceClass.LOOPBACK), 1)
        self.assertEqual(int(InterfaceClass.BRIDGE), 2)
        self.assertEqual(int(InterfaceClass.WIRED), 3)
        self.assertEqual(int(InterfaceClass.WIRELESS), 4)
        self.assertEqual(int(InterfaceClass.TUNNEL), 5)
        return

    def test_interface_class_serialisation_round_trip(self) -> None:
        """
            Verify ``InterfaceClass(6)`` and ``InterfaceClass["VPN_OVERLAY"]``
            both yield the ``VPN_OVERLAY`` member.
        """
        from_int = InterfaceClass(6)
        from_name = InterfaceClass["VPN_OVERLAY"]
        self.assertIs(from_int, InterfaceClass.VPN_OVERLAY)
        self.assertIs(from_name, InterfaceClass.VPN_OVERLAY)
        return


class InterfaceDescriptorTests(unittest.TestCase):
    """
        Construction tests for :class:`InterfaceDescriptor`.
    """

    def test_descriptor_wired_no_provider_ok(self) -> None:
        """
            Verify a wired descriptor without a provider constructs.
        """
        d = InterfaceDescriptor(name="eth0", interface_class=InterfaceClass.WIRED)
        self.assertEqual(d.name, "eth0")
        self.assertIsNone(d.provider)
        return

    def test_descriptor_overlay_with_provider_ok(self) -> None:
        """
            Verify an overlay descriptor with a valid provider constructs.
        """
        d = InterfaceDescriptor(
            name="tailscale0",
            interface_class=InterfaceClass.VPN_OVERLAY,
            provider="tailscale",
        )
        self.assertEqual(d.provider, "tailscale")
        return

    def test_descriptor_overlay_without_provider_raises(self) -> None:
        """
            Verify ``VPN_OVERLAY`` without a provider raises.
        """
        with self.assertRaises(ConfigurationError):
            InterfaceDescriptor(
                name="tailscale0",
                interface_class=InterfaceClass.VPN_OVERLAY,
                provider=None,
            )
        return

    def test_descriptor_non_overlay_with_provider_raises(self) -> None:
        """
            Verify a non-overlay class with a provider raises.
        """
        with self.assertRaises(ConfigurationError):
            InterfaceDescriptor(
                name="eth0",
                interface_class=InterfaceClass.WIRED,
                provider="tailscale",
            )
        return

    def test_descriptor_overlay_unsupported_provider_raises(self) -> None:
        """
            Verify an unsupported provider value raises.
        """
        with self.assertRaises(ConfigurationError):
            InterfaceDescriptor(
                name="tailscale0",
                interface_class=InterfaceClass.VPN_OVERLAY,
                provider="nordvpn",
            )
        return


class DetectOverlayProviderTests(unittest.TestCase):
    """
        Table-driven tests for :func:`detect_overlay_provider`.
    """

    def test_detect_overlay_provider_table(self) -> None:
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
            self.assertEqual(actual, expected, f"ifname={ifname!r}")
        return


if __name__ == "__main__":
    unittest.main()
