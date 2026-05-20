"""
    .. module:: test_vpnoverlayprofile
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Unit tests for :mod:`automojo.networking.vpnoverlayprofile`.

    .. moduleauthor:: Automojo Test Author
"""

import logging
import unittest

from automojo.errors.exceptions import ConfigurationError
from automojo.networking.vpnoverlayprofile import (
    SUPPORTED_VPN_PROVIDERS,
    VPNOverlayProfile,
)


class ConstructionTests(unittest.TestCase):
    """
        Construction-path tests for :class:`VPNOverlayProfile`.
    """

    def test_construction_with_complete_payload(self) -> None:
        """
            Verify a complete payload constructs successfully and the
            stored field values match.
        """
        profile = VPNOverlayProfile(
            name="lab-overlay",
            provider="tailscale",
            network="acme.ts.net",
            tags=("tag:lab",),
            dns_suffix="acme.ts.net",
            magic_dns_enabled=True,
            acl_ref="acls/lab.json",
        )
        self.assertEqual(profile.name, "lab-overlay")
        self.assertEqual(profile.provider, "tailscale")
        self.assertEqual(profile.network, "acme.ts.net")
        self.assertEqual(profile.tags, ("tag:lab",))
        self.assertEqual(profile.dns_suffix, "acme.ts.net")
        self.assertTrue(profile.magic_dns_enabled)
        self.assertEqual(profile.acl_ref, "acls/lab.json")
        return

    def test_construction_empty_name_raises(self) -> None:
        """
            Verify an empty ``name`` raises :class:`ConfigurationError`.
        """
        with self.assertRaises(ConfigurationError):
            VPNOverlayProfile(name="", provider="tailscale", network="acme.ts.net")
        return

    def test_construction_whitespace_name_raises(self) -> None:
        """
            Verify a ``name`` containing whitespace raises.
        """
        with self.assertRaises(ConfigurationError):
            VPNOverlayProfile(name="lab overlay", provider="tailscale", network="acme.ts.net")
        return

    def test_construction_unknown_provider_raises(self) -> None:
        """
            Verify an unsupported ``provider`` value raises.
        """
        with self.assertRaises(ConfigurationError):
            VPNOverlayProfile(name="lab", provider="nordvpn", network="acme.ts.net")
        return

    def test_supported_providers_constant(self) -> None:
        """
            Verify the supported providers constant has the expected entries.
        """
        self.assertIn("tailscale", SUPPORTED_VPN_PROVIDERS)
        self.assertIn("twingate", SUPPORTED_VPN_PROVIDERS)
        return


class FromDictTests(unittest.TestCase):
    """
        ``from_dict`` parsing tests.
    """

    def test_from_dict_round_trip(self) -> None:
        """
            Verify a complete YAML-shaped dict round-trips into an equal profile.
        """
        data = {
            "name": "lab-overlay",
            "provider": "tailscale",
            "network": "acme.ts.net",
            "tags": ["tag:lab"],
            "dns_suffix": "acme.ts.net",
            "magic_dns_enabled": True,
            "acl_ref": "acls/lab.json",
        }
        profile = VPNOverlayProfile.from_dict(data=data)
        expected = VPNOverlayProfile(
            name="lab-overlay",
            provider="tailscale",
            network="acme.ts.net",
            tags=("tag:lab",),
            dns_suffix="acme.ts.net",
            magic_dns_enabled=True,
            acl_ref="acls/lab.json",
        )
        self.assertEqual(profile, expected)
        self.assertEqual(profile.tags, ("tag:lab",))
        return

    def test_from_dict_missing_keys_raises_with_list(self) -> None:
        """
            Verify the error message lists the missing required keys.
        """
        data = {"provider": "tailscale"}
        with self.assertRaises(ConfigurationError) as ctx:
            VPNOverlayProfile.from_dict(data=data)
        msg = str(ctx.exception)
        self.assertIn("name", msg)
        self.assertIn("network", msg)
        return

    def test_from_dict_ignores_unknown_keys_with_warning(self) -> None:
        """
            Verify unknown keys are ignored with a logger warning.
        """
        data = {
            "name": "lab",
            "provider": "twingate",
            "network": "acme.twingate.com",
            "weird_field": 42,
        }
        with self.assertLogs("automojo.networking.vpnoverlayprofile", level=logging.WARNING) as captured:
            profile = VPNOverlayProfile.from_dict(data=data)
        self.assertEqual(profile.provider, "twingate")
        joined = "\n".join(captured.output)
        self.assertIn("weird_field", joined)
        return


class EqualityAndHashingTests(unittest.TestCase):
    """
        Frozen-dataclass hash and equality behaviour.
    """

    def test_equal_profiles_hash_identically(self) -> None:
        """
            Verify two equally-constructed profiles compare equal and
            hash identically, and are usable as a dict key.
        """
        a = VPNOverlayProfile(name="lab", provider="tailscale", network="acme.ts.net")
        b = VPNOverlayProfile(name="lab", provider="tailscale", network="acme.ts.net")
        self.assertEqual(a, b)
        self.assertEqual(hash(a), hash(b))
        bucket = {a: "value"}
        self.assertEqual(bucket[b], "value")
        return


class EffectiveDnsSuffixTests(unittest.TestCase):
    """
        :meth:`VPNOverlayProfile.effective_dns_suffix` tests.
    """

    def test_effective_dns_suffix_returns_field_verbatim(self) -> None:
        """
            Verify the suffix string is returned regardless of the
            ``magic_dns_enabled`` flag.
        """
        profile_a = VPNOverlayProfile(
            name="lab",
            provider="tailscale",
            network="acme.ts.net",
            dns_suffix="acme.ts.net",
            magic_dns_enabled=True,
        )
        profile_b = VPNOverlayProfile(
            name="lab",
            provider="tailscale",
            network="acme.ts.net",
            dns_suffix="acme.ts.net",
            magic_dns_enabled=False,
        )
        self.assertEqual(profile_a.effective_dns_suffix(), "acme.ts.net")
        self.assertEqual(profile_b.effective_dns_suffix(), "acme.ts.net")
        return

    def test_magic_dns_enabled_with_no_suffix_accepted(self) -> None:
        """
            Verify ``magic_dns_enabled=True`` with ``dns_suffix=None`` is
            accepted (the field combination is legal — the resolver
            decides at runtime).
        """
        profile = VPNOverlayProfile(
            name="lab",
            provider="tailscale",
            network="acme.ts.net",
            dns_suffix=None,
            magic_dns_enabled=True,
        )
        self.assertIsNone(profile.effective_dns_suffix())
        self.assertTrue(profile.magic_dns_enabled)
        return


if __name__ == "__main__":
    unittest.main()
